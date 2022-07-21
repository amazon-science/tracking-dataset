import json
import subprocess
import sys
import urllib
import zipfile

from collections import defaultdict
from pathlib import Path

if __name__ == "__main__":
    S3_URL = "s3://tracking-dataset-eccv-2022/"

    script_dir = Path(__file__).parent
    dataset_dir = script_dir / "dataset"

    subprocess.run([sys.executable, "-m", "awscli", "s3", "sync", "--no-sign-request", S3_URL, dataset_dir])

    anno_zips = ["anno_amodal.zip", "anno_visible.zip"]
    anno_zips = [Path("annotation", v) for v in anno_zips]
    zip_subpaths = anno_zips + ["raw_data/videos.zip"]
    for zip_subpath in zip_subpaths:
        zip_path = dataset_dir / zip_subpath
        print(f"Extracting {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(zip_path.parent)

    # pathtrack_download_url = "https://data.vision.ee.ethz.ch/daid/MOT/pathtrack_release_v1.0.zip"
    # meva_s3_url = "s3://mevadata-public-01/drops-123-r13/"
    # # % aws s3 ls s3://mevadata-public-01/drops-123-r13/2018-03-07/16/2018-03-07.16-50-00.16-55-00.bus.G331.r13.avi
    # virat_page = "https://data.kitware.com/#collection/56f56db28d777f753209ba9f/folder/56f581ce8d777f753209ca43"
    # pixabay_url_base = "https://pixabay.com/videos/"
    #
    # external_video_id_mapping = {
    #     "Meva": {
    #         "2018-03-07.16-50-00.16-55-00.bus.G331_0-180000.mp4": "uid_vid_00102.mp4",
    #         "2018-03-15.15-10-00.15-15-00.bus.G331_180000-300300.mp4": "uid_vid_00103.mp4",
    #         "2018-03-13.17-40-00.17-41-19.school.G421_0-79500.mp4": "uid_vid_00104.mp4",
    #         "2018-03-09.10-15-01.10-20-01.school.G420_180000-300033.mp4": "uid_vid_00105.mp4",
    #         "2018-03-15.15-35-00.15-40-00.school.G421_180000-300066.mp4": "uid_vid_00106.mp4",
    #         "2018-03-07.16-50-00.16-55-00.bus.G331_180000-300166.mp4": "uid_vid_00107.mp4",
    #         "2018-03-13.15-55-00.16-00-00.school.G421_0-180000.mp4": "uid_vid_00108.mp4",
    #         "2018-03-07.16-55-01.17-00-00.bus.G508_0-180000.mp4": "uid_vid_00109.mp4",
    #         "2018-03-07.16-50-00.16-55-00.school.G421_180000-300066.mp4": "uid_vid_00110.mp4",
    #         "2018-03-11.16-35-01.16-40-01.school.G420_180000-300033.mp4": "uid_vid_00111.mp4",
    #         "2018-03-15.15-10-00.15-15-00.bus.G331_0-180000.mp4": "uid_vid_00112.mp4",
    #         "2018-03-15.15-35-00.15-40-00.school.G421_0-180000.mp4": "uid_vid_00113.mp4",
    #         "2018-03-13.15-55-00.16-00-00.school.G421_180000-300000.mp4": "uid_vid_00114.mp4",
    #         "2018-03-15.14-50-00.14-55-00.bus.G508_0-180000.mp4": "uid_vid_00115.mp4",
    #         "2018-03-15.14-50-00.14-55-00.bus.G508_180000-300000.mp4": "uid_vid_00116.mp4",
    #         "2018-03-07.16-50-00.16-55-00.school.G421_0-180000.mp4": "uid_vid_00117.mp4"
    #     },
    #     "PathTrack": {
    #         "yZde6KWbWuM_0_7": "uid_vid_00118.mp4",
    #         "1ifHYTW_AU0_674_680": "uid_vid_00119.mp4",
    #         "OabhIVN8Pps_1_22": "uid_vid_00120.mp4",
    #         "2DiQUX11YaY_4_11": "uid_vid_00121.mp4",
    #         "HlvCV1YtJFI_127_132": "uid_vid_00122.mp4",
    #         "Twfy_jWEDt4_40_46": "uid_vid_00123.mp4",
    #         "03tAll3Rnb8_145_160": "uid_vid_00124.mp4",
    #         "EjekbTQT2dw_129_155": "uid_vid_00125.mp4",
    #         "1k9qcUaw_ZY_92_106": "uid_vid_00126.mp4",
    #         "CcevP4Dgocw_55_66": "uid_vid_00127.mp4",
    #         "0Xtp77A4zF4_8_84": "uid_vid_00128.mp4",
    #         "D8RppPVMWAM_0_18": "uid_vid_00129.mp4",
    #         "Bqn_GzsrDqM_174_182": "uid_vid_00130.mp4",
    #         "CqusBYOcaA4_639_647": "uid_vid_00131.mp4",
    #         "xnHDu-oW7_Y_871_879": "uid_vid_00132.mp4",
    #         "6EWOHAs2CeY_116_127": "uid_vid_00133.mp4",
    #         "wt9UHXJ1kRU_0_15": "uid_vid_00134.mp4",
    #         "881uK5SDnFU_26_55": "uid_vid_00135.mp4",
    #         "L4H-nBgiFmg_212_226": "uid_vid_00136.mp4",
    #         "2_tnrvMIt2E_99_135": "uid_vid_00137.mp4",
    #         "SM4dmuL8KKw_13_28": "uid_vid_00138.mp4",
    #         "iSJqd8z1v20_0_13": "uid_vid_00139.mp4",
    #         "HzOiJ87yNIg_237_262": "uid_vid_00140.mp4",
    #         "h2hwIDQkzBE_12_27": "uid_vid_00141.mp4",
    #         "WAUYbr5YE2U_0_13": "uid_vid_00142.mp4",
    #         "WKbN-iY7DSU_42_53": "uid_vid_00143.mp4"
    #     },
    #     "Virat": {
    #         "VIRAT_S_010201_04_000374_000469.mp4": "uid_vid_00144.mp4",
    #         "VIRAT_S_010203_06_000620_000760.mp4": "uid_vid_00145.mp4",
    #         "VIRAT_S_010203_08_000895_000975.mp4": "uid_vid_00146.mp4",
    #         "VIRAT_S_010004_06_000547_000715.mp4": "uid_vid_00147.mp4",
    #         "VIRAT_S_010208_06_000671_000744.mp4": "uid_vid_00148.mp4",
    #         "VIRAT_S_010200_07_000748_000837.mp4": "uid_vid_00149.mp4",
    #         "VIRAT_S_010004_08_000811_000920.mp4": "uid_vid_00150.mp4",
    #         "VIRAT_S_010200_00_000060_000218.mp4": "uid_vid_00151.mp4",
    #         "VIRAT_S_010203_07_000775_000869.mp4": "uid_vid_00152.mp4"
    #     },
    #     "Pixabay": {
    #         "lord-street-liverpool-city-28889": "uid_vid_00162.mp4",
    #         "people-alley-street-ukraine-bike-39836": "uid_vid_00232.mp4",
    #         "india-street-busy-rickshaw-people-3175": "uid_vid_00233.mp4",
    #         "lima-building-street-people-32242": "uid_vid_00234.mp4",
    #         "street-people-city-urban-walking-33572": "uid_vid_00235.mp4",
    #         "thailand-bangkok-airport-aircraft-30872": "uid_vid_00236.mp4"
    #     }
    # }
