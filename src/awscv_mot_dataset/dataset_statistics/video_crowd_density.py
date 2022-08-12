

from awscv_motion_dataset.dataset import AWSCVMotionDataset, DataSample

from .stat_utils import correct_timestamp


def remove_ignore_entities(sample: DataSample):
    sample_copy = sample.get_copy_without_entities()

    # sample = correct_timestamp(sample)
    unique_ids = set([x.id for x in sample.entities])

    for u_id in unique_ids:
        track = sample.get_entities_with_id(u_id)
        person_track = [x for x in track if 'person' in x.labels]

        if len(person_track) > 0:
            timestamps = [x.time for x in person_track]
            timestamps = sorted(timestamps)
            duration = timestamps[-1] - timestamps[0]

            if duration >= 1000:
                for entity in person_track:
                    sample_copy.add_entity(entity)

    return sample_copy


def crowd_density_for_video(sample: DataSample):

    sample = remove_ignore_entities(sample)
    frame_inds = sample.get_non_empty_frames()

    num_entities = 0
    for frame_ind in frame_inds:
        entities = sample.get_entities_for_frame_num(frame_ind)
        entities = [x for x in entities if 'person' in x.labels]

        num_entities += len(entities)

    return num_entities / len(frame_inds)


def crowd_density(dataset: AWSCVMotionDataset):

    samples = list(dataset.train_samples)
    crowd_density_list = []

    for sample_id, sample in samples:
        avg_density = crowd_density_for_video(sample)
        crowd_density_list.append(avg_density)

    return crowd_density_list