from exp_base import *

############## choose an experiment ##############

current = 'builder'
current = 'trainer'

mod = '"eg00"' # nothing; builder
mod = '"eg01"' # deleted junk
mod = '"eg02"' # added hyps
mod = '"eg03"' # train a while
mod = '"eg04"' # 1 scale

############## exps ##############

exps['builder'] = [
    'carla_ego', # mode
    'carla_traj_10_data', # dataset
    'carla_bounds', 
    '3_iters',
    'lr0',
    'B1',
    'no_shuf',
    'train_feat3d',
    'train_ego',
    'log1',
]
exps['trainer'] = [
    'carla_ego', # mode
    'carla_traj_10_data', # dataset
    'carla_bounds', 
    '10k_iters',
    'lr4',
    'B1',
    'train_feat3d',
    'train_ego',
    'log50',
]

############## groups ##############

groups['carla_ego'] = ['do_carla_ego = True']

groups['train_feat3d'] = [
    'do_feat3d = True',
    'feat3d_dim = 32',
    'feat3d_smooth_coeff = 0.01',
]
groups['train_ego'] = [
    'do_ego = True',
    'ego_t_l2_coeff = 1.0',
    'ego_deg_l2_coeff = 1.0',
    'ego_num_rots = 11',
    'ego_rot_max = 4.0',
    'ego_num_scales = 1',
    'ego_max_disp_h = 1',
    'ego_max_disp_w = 2',
    'ego_max_disp_d = 2',
    'ego_synth_prob = 0.5',
]

############## datasets ##############

# dims for mem
SIZE = 32
Z = int(SIZE*4)
Y = int(SIZE*1)
X = int(SIZE*4)
K = 2 # how many objects to consider
N = 8 # how many objects per npz
S = 2
H = 128
W = 384
# H and W for proj stuff
PH = int(H/2.0)
PW = int(W/2.0)

dataset_location = "/projects/katefgroup/datasets/carla/processed/npzs"

groups['carla_traj_10_data'] = [
    'dataset_name = "carla"',
    'H = %d' % H,
    'W = %d' % W,
    'trainset = "taqs100i2ten"',
    'trainset_format = "traj"', 
    'trainset_consec = False', 
    'trainset_seqlen = %d' % S, 
    'dataset_location = "%s"' % dataset_location,
    'dataset_filetype = "npz"'
]
groups['carla_multiview_train_data'] = [
    'dataset_name = "carla"',
    'H = %d' % H,
    'W = %d' % W,
    'trainset = "mags7i3t"',
    'trainset_format = "multiview"', 
    'trainset_seqlen = %d' % S, 
    'dataset_location = "%s"' % dataset_location,
    'dataset_filetype = "npz"'
]
groups['carla_multiview_test_data'] = [
    'dataset_name = "carla"',
    'H = %d' % H,
    'W = %d' % W,
    'testset = "mags7i3v"',
    'testset_format = "multiview"', 
    'testset_seqlen = %d' % S, 
    'dataset_location = "%s"' % dataset_location,
    'dataset_filetype = "npz"'
]
groups['carla_multiview_train_val_data'] = [
    'dataset_name = "carla"',
    'H = %d' % H,
    'W = %d' % W,
    'trainset = "mags7i3t"',
    'trainset_format = "multiview"', 
    'trainset_seqlen = %d' % S, 
    'valset = "mags7i3v"',
    'valset_format = "multiview"', 
    'valset_seqlen = %d' % S, 
    'dataset_location = "%s"' % dataset_location,
    'dataset_filetype = "npz"'
]

############## verify and execute ##############

def _verify_(s):
    varname, eq, val = s.split(' ')
    assert varname in globals()
    assert eq == '='
    assert type(s) is type('')

print(current)
assert current in exps
for group in exps[current]:
    print("  " + group)
    assert group in groups
    for s in groups[group]:
        print("    " + s)
        _verify_(s)
        exec(s)

s = "mod = " + mod
_verify_(s)

exec(s)