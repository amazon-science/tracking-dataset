import json
import os
import requests
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as XMLTree
import zipfile

from pathlib import Path
from tqdm import tqdm

FFMPEG_BASE_CMD = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]


def copy_to_target(src_path, tgt_path):
    # Try to get the video fps as a test before copying
    get_vid_fps(src_path)
    src_path = Path(src_path)
    src_tmp_path = src_path.with_name(f"{src_path.stem}_copy{src_path.suffix}")
    shutil.copy2(src_path, src_tmp_path)
    src_tmp_path.rename(tgt_path)


def run_with_tmp_dir(cmd_fn, out_path):
    if isinstance(cmd_fn, list):
        cmd = cmd_fn
        def cmd_fn(tmp_file_path):
            fullcmd = cmd + [tmp_file_path]
            return subprocess.run(fullcmd, check=True)
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_file_path = Path(tmp_path, Path(out_path).name)
        ret = cmd_fn(tmp_file_path)
        subprocess.run(["mv", tmp_file_path, out_path], check=True)
    return ret


def write_img_files_to_vid_ffmpeg(out_file, in_files, fps):
    input_str = "'\nfile '".join([str(p) for p in in_files])
    input_str = "file '" + input_str + "'\n"

    cmd = [*FFMPEG_BASE_CMD,
           "-f", "concat", "-safe", "0", "-r", str(fps), "-i", "/dev/stdin",
           "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2"]

    def run_cmd(tmp_file_path):
        fullcmd = cmd + [tmp_file_path]
        return subprocess.run(fullcmd, input=input_str.encode('utf-8'), check=True)

    return run_with_tmp_dir(run_cmd, out_file)


def crop_vid_ffmpeg(vid_in_path, crop_out_path, ts_ms_start, ts_ms_end, fps=None, end_pad_ms=1):
    # Pad end time with 1 since end times are exclusive according to this SO post: https://stackoverflow.com/a/52916510
    t1_secs, t2_secs = [t / 1000.0 for t in (ts_ms_start, ts_ms_end + end_pad_ms)]
    # Hack to not provide a start seek if t1_secs is 0 due to an ffmpeg issue where it can't seek to 0 on some videos
    start_seek_args = ["-ss", "{:.3f}".format(t1_secs)] if t1_secs else []
    fps_args = ["-r", str(fps)] if fps else []
    cmd = [
        *FFMPEG_BASE_CMD,
        *start_seek_args,
        "-i", vid_in_path,
        "-t", "{:.3f}".format(t2_secs - t1_secs),
        *fps_args,
        "-strict", "experimental",
    ]

    return run_with_tmp_dir(cmd, crop_out_path)


def convert_vid_ffmpeg(in_path, out_path, crf=None, copy=False, fps=None, fps_filter=False):
    # muxing queue size bug workaround: https://stackoverflow.com/questions/49686244/ffmpeg-too-many-packets-buffered-for-output-stream-01
    crf_args = ["-crf", str(crf)] if crf else []
    copy_args = ["-c", "copy"] if copy else []
    if fps:
        if fps_filter:
            fps_args = ["-filter:v", f"fps={fps}"]
        else:
            fps_args = ["-r", str(fps)]
    else:
        fps_args = []
    cmd = [*FFMPEG_BASE_CMD, "-i", in_path, *crf_args, *copy_args, *fps_args, "-max_muxing_queue_size", "99999"]
    return run_with_tmp_dir(cmd, out_path)


def get_vid_fps(vid_path):
    probe_json = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-of", "json", "-show_entries",
         "stream=r_frame_rate", vid_path], stdout=subprocess.PIPE, check=True)
    probe_obj = json.loads(probe_json.stdout)
    fps_str = probe_obj["streams"][0]["r_frame_rate"]
    fps_numer, fps_denom = (int(s) for s in fps_str.split("/"))
    fps = fps_numer / fps_denom
    return fps


def get_pixabay_vids(pixabay_mapping, videos_root):
    pixabay_url_home = "https://pixabay.com"
    pixabay_download_template = pixabay_url_home + "/videos/download/video-{}_source.mp4?attachment"

    out_dir = videos_root / "pixabay"
    out_dir.mkdir(exist_ok=True)

    print(f"Downloading Pixabay")

    # Approach from: https://stackoverflow.com/a/63770219
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }

    session = requests.Session()
    session.headers.update(headers)

    # --- get cookies ---
    r = session.get(pixabay_url_home)

    # --- get videos ---
    for pixa_id, uid in tqdm(pixabay_mapping.items()):
        try:
            download_out_path = out_dir / (pixa_id + ".mp4")
            final_vid_path = videos_root / uid
            if not download_out_path.exists():
                print(f"Downloading {download_out_path}")
                pixa_vid_num = pixa_id.rsplit("-", 1)[-1]
                url = pixabay_download_template.format(pixa_vid_num)
                response = session.get(url)
                with open(download_out_path, "wb") as f:
                    f.write(response.content)

            fps = get_vid_fps(download_out_path)
            if fps > 31:
                new_fps = fps / 2
                new_fps_path = download_out_path.with_name(f"{download_out_path.stem}_newfps{download_out_path.suffix}")
                if not new_fps_path.exists():
                    print(f"Downsampling fps of {download_out_path}")
                    # The fps filter seems to align properly with the orig video while -r has slight misalignments
                    convert_vid_ffmpeg(download_out_path, new_fps_path, fps=new_fps, fps_filter=True)
            else:
                new_fps_path = download_out_path

            copy_to_target(new_fps_path, final_vid_path)
        except Exception as e:
            print(f"Failed to process pixabay video: {pixa_id}, for uid: {uid}, exception: {e}", file=sys.stderr)


def get_pathtrack_vids(pathtrack_mapping, videos_root):
    pathtrack_download_url = "https://data.vision.ee.ethz.ch/daid/MOT/pathtrack_release_v1.0.zip"

    out_dir = videos_root / "pathtrack"
    out_dir.mkdir(exist_ok=True)

    print(f"Downloading PathTrack")

    zip_out_path = out_dir / "pathtrack.zip"
    extracted_path = out_dir / "pathtrack_release"
    if not extracted_path.exists():
        if not zip_out_path.exists():
            download = True
        else:
            try:
                print(f"Testing zip: {zip_out_path}")
                with zipfile.ZipFile(zip_out_path) as zip_ref:
                    download = zip_ref.testzip() is not None
            except zipfile.BadZipFile as e:
                download = True
        if download:
            # Streaming as described here: https://stackoverflow.com/a/37573701
            print(f"Downloading pathtrack to {zip_out_path}")
            print(f"Please note this zip is over 30GB and can take hours to download")
            response = requests.get(pathtrack_download_url, stream=True)
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024 * 10
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
            with open(zip_out_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    f.write(data)
            progress_bar.close()
            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                raise Exception("Error downloading pathtrack")
        print(f"Extracting pathtrack {zip_out_path}", flush=True)
        with zipfile.ZipFile(zip_out_path) as zip_ref:
            zip_ref.extractall(zip_out_path.parent)

    for patht_id, uid in tqdm(pathtrack_mapping.items()):
        try:
            patht_root = extracted_path / "train" / patht_id
            if not patht_root.exists():
                patht_root = extracted_path / "test" / patht_id
            ffmpeg_out_file = patht_root / (patht_id + ".mp4")
            final_vid_path = videos_root / uid

            if not ffmpeg_out_file.exists():
                info_path = patht_root / "info.xml"
                info_xml = XMLTree.parse(info_path)
                info_root = info_xml.getroot().find("doc")
                def get_text(tag):
                    return info_root.find(tag).text
                fps = float(get_text('fps'))

                img_path = patht_root / "img1"
                input_paths = sorted(img_path.glob("*.jpg"))
                write_img_files_to_vid_ffmpeg(ffmpeg_out_file, input_paths, fps)
            copy_to_target(ffmpeg_out_file, final_vid_path)
        except Exception as e:
            print(f"Failed to process pathtrack video: {patht_id}, for uid: {uid}, exception: {e}", file=sys.stderr)


def get_virat_vids(virat_id_to_uid_and_urlid, videos_root):
    # virat_page = "https://data.kitware.com/#collection/56f56db28d777f753209ba9f/folder/56f581ce8d777f753209ca43"
    # e.g. download link https://data.kitware.com/api/v1/item/56f587f18d777f753209cc33/download
    # be careful of the 'file' urls instead of 'item', they work but the code is actually different
    virat_download_template = "https://data.kitware.com/api/v1/item/{}/download"

    out_dir = videos_root / "virat"
    out_dir.mkdir(exist_ok=True)

    print(f"Downloading Virat")

    for virat_id, (uid, down_code) in tqdm(virat_id_to_uid_and_urlid.items()):
        try:
            download_out_path = out_dir / virat_id
            final_vid_path = videos_root / uid
            if not download_out_path.exists():
                print(f"Downloading {download_out_path}")
                url = virat_download_template.format(down_code)
                response = requests.get(url)
                with open(download_out_path, "wb") as f:
                    f.write(response.content)
            copy_to_target(download_out_path, final_vid_path)
        except Exception as e:
            print(f"Failed to process virat video: {virat_id}, for uid: {uid}, exception: {e}", file=sys.stderr)


def get_meva_vids(meva_mapping, videos_root):
    # meva_s3_url = "s3://mevadata-public-01/drops-123-r13/"
    # aws s3 ls s3://mevadata-public-01/drops-123-r13/2018-03-07/16/2018-03-07.16-50-00.16-55-00.bus.G331.r13.avi
    meva_download_template = "s3://mevadata-public-01/drops-123-r13/{date}/{hour}/{fname}"

    out_dir = videos_root / "meva"
    out_dir.mkdir(exist_ok=True)

    print(f"Downloading Meva")

    for meva_id, uid in tqdm(meva_mapping.items()):
        try:
            meva_fname_base, fname_timestamp = meva_id.rsplit("_", 1)
            ts_ms_start, ts_ms_end = [int(x) for x in Path(fname_timestamp).stem.split("-")]
            meva_url_fname = meva_fname_base + ".r13.avi"
            download_out_path = out_dir / (meva_url_fname)
            final_vid_path = videos_root / uid
            if not download_out_path.exists():
                # print(f"Downloading {download_out_path}")
                meva_date = meva_url_fname[:10]
                meva_hour = meva_url_fname[20:22]  # Don't use [11:13], that's not the hour used actually
                url = meva_download_template.format(date=meva_date, hour=meva_hour, fname=meva_url_fname)
                subprocess.run([sys.executable,
                                "-m", "awscli", "s3", "cp", "--no-sign-request", url, download_out_path], check=True)

            mp4_out_path = download_out_path.with_suffix(".mp4")
            # mp4_out_path = download_out_path
            if not mp4_out_path.exists():
                print(f"Converting {download_out_path.name} to mp4")
                # Convert to mp4 first or there are some weird time issues (e.g. only 2:59 instead of 3:00)
                convert_vid_ffmpeg(download_out_path, mp4_out_path, copy=True)
                # convert_vid_ffmpeg(download_out_path, mp4_out_path, crf=17)

            crop_out_path = out_dir / meva_id
            if not crop_out_path.exists():
                print(f"Cropping {mp4_out_path.name} to {crop_out_path.name}")
                # Original dataset meva videos were cropped with 15 fps
                crop_vid_ffmpeg(mp4_out_path, crop_out_path, ts_ms_start, ts_ms_end, fps=15, end_pad_ms=0)
            copy_to_target(crop_out_path, final_vid_path)
        except Exception as e:
            print(f"Failed to process meva video: {meva_id}, for uid: {uid}, exception: {e}", file=sys.stderr)


virat_id_to_uid_and_urlid = {
        "VIRAT_S_010201_04_000374_000469.mp4": ("uid_vid_00144.mp4", "56f587f18d777f753209cc33"),
        "VIRAT_S_010203_06_000620_000760.mp4": ("uid_vid_00145.mp4", "56f587fd8d777f753209cc63"),
        "VIRAT_S_010203_08_000895_000975.mp4": ("uid_vid_00146.mp4", "56f588008d777f753209cc69"),
        "VIRAT_S_010004_06_000547_000715.mp4": ("uid_vid_00147.mp4", "56f587a38d777f753209cb58"),
        "VIRAT_S_010208_06_000671_000744.mp4": ("uid_vid_00148.mp4", "56f588208d777f753209ccdb"),
        "VIRAT_S_010200_07_000748_000837.mp4": ("uid_vid_00149.mp4", "56f587ec8d777f753209cc1b"),
        "VIRAT_S_010004_08_000811_000920.mp4": ("uid_vid_00150.mp4", "56f587a68d777f753209cb5e"),
        "VIRAT_S_010200_00_000060_000218.mp4": ("uid_vid_00151.mp4", "56f587e78d777f753209cc06"),
        "VIRAT_S_010203_07_000775_000869.mp4": ("uid_vid_00152.mp4", "56f587ff8d777f753209cc66"),
}

external_video_id_mapping = {
    "Pixabay": {
        "lord-street-liverpool-city-28889": "uid_vid_00162.mp4",
        "people-alley-street-ukraine-bike-39836": "uid_vid_00232.mp4",
        "india-street-busy-rickshaw-people-3175": "uid_vid_00233.mp4",
        "lima-building-street-people-32242": "uid_vid_00234.mp4",
        "street-people-city-urban-walking-33572": "uid_vid_00235.mp4",
        "thailand-bangkok-airport-aircraft-30872": "uid_vid_00236.mp4"
    },
    "PathTrack": {
        "yZde6KWbWuM_0_7": "uid_vid_00118.mp4",
        "1ifHYTW_AU0_674_680": "uid_vid_00119.mp4",
        "OabhIVN8Pps_1_22": "uid_vid_00120.mp4",
        "2DiQUX11YaY_4_11": "uid_vid_00121.mp4",
        "HlvCV1YtJFI_127_132": "uid_vid_00122.mp4",
        "Twfy_jWEDt4_40_46": "uid_vid_00123.mp4",
        "03tAll3Rnb8_145_160": "uid_vid_00124.mp4",
        "EjekbTQT2dw_129_155": "uid_vid_00125.mp4",
        "1k9qcUaw_ZY_92_106": "uid_vid_00126.mp4",
        "CcevP4Dgocw_55_66": "uid_vid_00127.mp4",
        "0Xtp77A4zF4_8_84": "uid_vid_00128.mp4",
        "D8RppPVMWAM_0_18": "uid_vid_00129.mp4",
        "Bqn_GzsrDqM_174_182": "uid_vid_00130.mp4",
        "CqusBYOcaA4_639_647": "uid_vid_00131.mp4",
        "xnHDu-oW7_Y_871_879": "uid_vid_00132.mp4",
        "6EWOHAs2CeY_116_127": "uid_vid_00133.mp4",
        "wt9UHXJ1kRU_0_15": "uid_vid_00134.mp4",
        "881uK5SDnFU_26_55": "uid_vid_00135.mp4",
        "L4H-nBgiFmg_212_226": "uid_vid_00136.mp4",
        "2_tnrvMIt2E_99_135": "uid_vid_00137.mp4",
        "HzOiJ87yNIg_237_262": "uid_vid_00140.mp4",
        "h2hwIDQkzBE_12_27": "uid_vid_00141.mp4",
        "WAUYbr5YE2U_0_13": "uid_vid_00142.mp4",
        "WKbN-iY7DSU_42_53": "uid_vid_00143.mp4"
    },
    "Meva": {
        "2018-03-07.16-50-00.16-55-00.bus.G331_0-180000.mp4": "uid_vid_00102.mp4",
        "2018-03-15.15-10-00.15-15-00.bus.G331_180000-300300.mp4": "uid_vid_00103.mp4",
        "2018-03-13.17-40-00.17-41-19.school.G421_0-79500.mp4": "uid_vid_00104.mp4",
        "2018-03-09.10-15-01.10-20-01.school.G420_180000-300033.mp4": "uid_vid_00105.mp4",
        "2018-03-15.15-35-00.15-40-00.school.G421_180000-300066.mp4": "uid_vid_00106.mp4",
        "2018-03-07.16-50-00.16-55-00.bus.G331_180000-300166.mp4": "uid_vid_00107.mp4",
        "2018-03-13.15-55-00.16-00-00.school.G421_0-180000.mp4": "uid_vid_00108.mp4",
        "2018-03-07.16-55-01.17-00-00.bus.G508_0-180000.mp4": "uid_vid_00109.mp4",
        "2018-03-07.16-50-00.16-55-00.school.G421_180000-300066.mp4": "uid_vid_00110.mp4",
        "2018-03-11.16-35-01.16-40-01.school.G420_180000-300033.mp4": "uid_vid_00111.mp4",
        "2018-03-15.15-10-00.15-15-00.bus.G331_0-180000.mp4": "uid_vid_00112.mp4",
        "2018-03-15.15-35-00.15-40-00.school.G421_0-180000.mp4": "uid_vid_00113.mp4",
        "2018-03-13.15-55-00.16-00-00.school.G421_180000-300000.mp4": "uid_vid_00114.mp4",
        "2018-03-15.14-50-00.14-55-00.bus.G508_0-180000.mp4": "uid_vid_00115.mp4",
        "2018-03-15.14-50-00.14-55-00.bus.G508_180000-300000.mp4": "uid_vid_00116.mp4",
        "2018-03-07.16-50-00.16-55-00.school.G421_0-180000.mp4": "uid_vid_00117.mp4"
    },
    "Virat": {k: v[0] for k, v in virat_id_to_uid_and_urlid.items()},
}


def download_core_dataset(s3_base_url, dataset_dir):
    anno_files = ["anno_amodal.zip", "anno_visible.zip", "splits.json"]
    anno_subpaths = [Path("annotation", v) for v in anno_files]
    video_subpaths = ["raw_data/videos.zip"]
    core_subpaths = anno_subpaths + video_subpaths
    for subpath in core_subpaths:
        fullpath = dataset_dir / subpath
        if not fullpath.exists():
            s3_url = os.path.join(s3_base_url, str(subpath))
            print(f"Downloading {s3_url} to {fullpath}")
            cmd = [sys.executable, "-m", "awscli", "s3", "cp", "--no-sign-request", s3_url, fullpath]
            subprocess.run(cmd, check=True)
            if fullpath.suffix == ".zip":
                print(f"Extracting {fullpath}", flush=True)
                with zipfile.ZipFile(fullpath, 'r') as zip_ref:
                    zip_ref.extractall(fullpath.parent)


def get_missing_and_corrupt_videos(videos_root):
    expected_uid_nums = set(list(range(237)) + [99999]) - {138, 139}
    expected_uid_vid_paths = set(videos_root / f"uid_vid_{str(i).zfill(5)}.mp4" for i in expected_uid_nums)
    # uid_vid_paths = set(videos_root.glob("uid_vid_*.mp4"))
    missing_vids = set()
    corrupt_vids = set()
    for expected_uid_vid_path in tqdm(expected_uid_vid_paths):
        if expected_uid_vid_path.exists():
            try:
                get_vid_fps(expected_uid_vid_path)
            except Exception as e:
                corrupt_vids.add(expected_uid_vid_path.name)
        else:
            missing_vids.add(expected_uid_vid_path.name)

    return missing_vids, corrupt_vids


if __name__ == "__main__":
    S3_URL = "s3://tracking-dataset-eccv-2022/dataset/"

    script_dir = Path(__file__).parent.resolve()
    dataset_dir = script_dir / "dataset" / "personpath22"
    videos_root = dataset_dir / "raw_data"

    print(f"Downloading dataset under {dataset_dir}. Please note there are many videos and this can take hours to"
          f" complete.")

    download_core_dataset(S3_URL, dataset_dir)
    get_pixabay_vids(external_video_id_mapping["Pixabay"], videos_root)
    get_virat_vids(virat_id_to_uid_and_urlid, videos_root)
    get_meva_vids(external_video_id_mapping["Meva"], videos_root)
    get_pathtrack_vids(external_video_id_mapping["PathTrack"], videos_root)

    print("Checking videos...")
    missing_vids, corrupt_vids = get_missing_and_corrupt_videos(videos_root)
    if missing_vids or corrupt_vids:
        print(f"Warning!!! There are missing and/or corrupt videos under {videos_root},"
              f" missing: {missing_vids}, corrupt: {corrupt_vids}."
              f" Please check the above output in the script to see the respective errors and refer to README.md for"
              f" potential fixes.", file=sys.stderr)
    else:
        print(f"Check successful. There are temporary files under the videos root path {videos_root},"
              f" in the folders: virat, meva, pixabay, and pathtrack, you can remove these folders once you have"
              f" verified all 236 uid*.mp4 videos are present and working")
