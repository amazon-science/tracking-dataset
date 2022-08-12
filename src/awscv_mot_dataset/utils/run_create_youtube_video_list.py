import argparse
import logging
import os
import cv2
import numpy as np

from dataclasses import dataclass

from src.awscv_mot_dataset.utils.io import load_json, load_csv, set_logger, save_csv, makedirs

from src.awscv_mot_dataset.utils.run_create_list_videos_from_manual_filtering import MANUAL_FILTERING_CVS_FILES_DIR

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from awscv_motion_dataset.utils.ingestion_utils import crop_video

_log = logging.getLogger(__name__)

MANUAL_FILTERING_CVS_FILES = [
    ('Youtube', 'Manual filtering_YouTube_12_01.csv'),
]

VIDEO_ROOT_DIR = '/workplace/data/motion_efs/academic_datasets/person_tracking/Youtube/raw_data'

# 100 MIN
MAX_VIDEO_LEN = int(100 * 60 * 1000)


@dataclass(frozen=True)
class VideoMetadata:
    source_name: str  # the name of the source (FillerStock, Virat, etc..)
    video_name: str  # the full path of the video
    video_clip_name: str  # the name of video clip
    web_player_url: str  # the web link to the visualizer
    is_useful_for_vanguard: bool

    keep_video: bool
    video_needs_to_be_edited: bool
    annotation_requires_special_handling: bool
    time_range: list


def parse_time_range_string(time_range_str: str):
    def parse_time_str(time_str: str):
        start_ind = time_str.find("'")
        end_ind = time_str.find("\"")
        time_ms = int(time_str[0:start_ind]) * 60 * 1000
        time_ms += int(time_str[start_ind + 1:end_ind]) * 1000

        return time_ms

    # replace abnormal token
    time_ranges = []
    time_range_str = time_range_str.replace("''", "\"")
    time_range_str = time_range_str.strip()
    if len(time_range_str) == 0:
        return time_ranges
    if time_range_str == "ALL":
        # maximum
        return [[0, MAX_VIDEO_LEN]]

    time_strings = time_range_str.split(';')
    for time_str in time_strings:
        tokens = time_str.split('-')
        if len(tokens) == 2:
            start_time = parse_time_str(tokens[0])
            end_time = parse_time_str(tokens[1])

            time_range = [start_time, end_time]
            time_ranges.append(time_range)
        else:
            print(f"Ignoring {time_str}")

    return time_ranges


def load_manual_filtering_csv_file(dataset_name, fname):
    """
    Takes as input a CVS file from the manual filtering, and outputs a list of VideoMetadata objects
    """
    _log.info('Opening {}'.format(fname))
    table = load_csv(fname)
    assert len(table) > 1, 'Empty table'
    header = table[0]

    def get_value_from_row(header, row, key, exact_match=False, return_None_if_not_found=False):
        # retrieve the row from the header
        if exact_match:
            idx_cols = np.where([key.lower() == _key.lower() for _key in header])[0]
        else:
            idx_cols = np.where([key.lower() in _key.lower() for _key in header])[0]

        # if key is not found, we just return None
        if return_None_if_not_found and len(idx_cols) == 0:
            return None

        # .. otherwise assert
        assert len(idx_cols) > 0, 'Cannot find column for key "{}"" in header "{}"'.format(key, header)
        assert len(idx_cols) <= 1, 'Found multiple columns for key "{}"" in header "{}"'.format(key, header)
        idx_col = idx_cols[0]

        # return the value
        return row[idx_col]

    meta_all = []
    for row in table[1:]:
        keep = get_value_from_row(header, row, 'Keep video')

        video_name = get_value_from_row(header, row, 'Video', exact_match=True)
        meta = VideoMetadata(source_name=dataset_name,
                             video_name=video_name,
                             web_player_url=get_value_from_row(header, row, 'Link'),
                             is_useful_for_vanguard=get_value_from_row(header, row, 'Useful for Vanguard',
                                                                       return_None_if_not_found=True),
                             keep_video=keep in ['Y', 'Y+', 'Y**', 'Y*'],
                             video_needs_to_be_edited=keep == 'Y+',
                             annotation_requires_special_handling=keep == 'Y**',
                             time_range=parse_time_range_string(
                                 get_value_from_row(header, row, 'Interesting time-ranges')),
                             video_clip_name=video_name,
                             )

        meta_all.append(meta)

    return meta_all


def process_videos(meta_all):
    shortlist_meta = []
    for meta in meta_all:
        if meta.keep_video:
            assert len(meta.time_range) > 0

            video_path = os.path.join(VIDEO_ROOT_DIR,
                                      'vids_chunked/vid_chunks_5m_Nonep',
                                      meta.video_name)
            vid = cv2.VideoCapture(video_path)
            height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
            fps = vid.get(cv2.CAP_PROP_FPS)
            frame_count = vid.get(cv2.CAP_PROP_FRAME_COUNT)
            video_len = int(frame_count * 1000 / fps)

            for time_range in meta.time_range:
                keep_video = meta.keep_video
                if width < 640 or height < 640:
                    keep_video = False

                start_time_ms = time_range[0]
                end_time_ms = min(time_range[1], video_len)

                if end_time_ms <= start_time_ms:
                    continue

                video_clip_name = f'chunks_of_interest/{meta.video_clip_name}_{start_time_ms}-{end_time_ms}.mp4'
                video_clip_path = os.path.join(VIDEO_ROOT_DIR, video_clip_name)
                os.makedirs(os.path.dirname(video_clip_path), exist_ok=True)

                if not os.path.exists(video_clip_path):
                    crop_video(video_path, video_clip_path, start_time_ms, end_time_ms, overwrite=True)
                    # ffmpeg_extract_subclip(video_path,
                    #                        start_time_ms / 1000,
                    #                        end_time_ms / 1000,
                    #                        targetname=video_clip_path)

                new_meta = VideoMetadata(source_name=meta.source_name,
                                         video_name=meta.video_name,
                                         web_player_url='http://motion.aka.corp.amazon.com:8200' + video_clip_path,
                                         is_useful_for_vanguard=meta.is_useful_for_vanguard,
                                         keep_video=keep_video,
                                         video_needs_to_be_edited=meta.video_needs_to_be_edited,
                                         annotation_requires_special_handling=meta.annotation_requires_special_handling,
                                         time_range=[start_time_ms, end_time_ms],
                                         video_clip_name=video_clip_name)

                shortlist_meta.append(new_meta)

    return shortlist_meta


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, required=True, help='output directory')
    return parser.parse_args()


def main():
    args = parse_args()
    makedirs(args.output_dir)
    set_logger(log_fname=os.path.join(args.output_dir, 'logger.log'))

    # load all the CSV files
    meta_all = []
    print(MANUAL_FILTERING_CVS_FILES)
    for dataset_name, csv_fname in MANUAL_FILTERING_CVS_FILES:
        meta_all.extend(
            load_manual_filtering_csv_file(dataset_name, os.path.join(MANUAL_FILTERING_CVS_FILES_DIR, csv_fname)))
    _log.info('Total number of processed videos: {}'.format(len(meta_all)))

    # process all videos
    meta_all = process_videos(meta_all)
    # remove the videos that we don't want to keep
    meta_all = [meta for meta in meta_all if meta.keep_video]

    # print some stats
    _log.info('Total number of videos to keep: {}'.format(len(meta_all)))
    _log.info('Number of videos that requires editing: {}'.format(
        len([meta for meta in meta_all if meta.video_needs_to_be_edited])))
    _log.info('Number of videos that require special annotation handling: {}'.format(
        len([meta for meta in meta_all if meta.annotation_requires_special_handling])))
    _log.info('Number of videos useful for Vanguard: {}'.format(
        len([meta for meta in meta_all if meta.is_useful_for_vanguard])))

    # saves the final summary table to the disk
    output_table_fname = os.path.join(args.output_dir, 'dataset.csv')
    table = [['source name', 'video_name', 'web_player_url']]
    for meta in meta_all:
        table.append([meta.source_name, meta.video_clip_name, meta.web_player_url])
    save_csv(table, output_table_fname)


if __name__ == '__main__':
    main()