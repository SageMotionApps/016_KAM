import torch
import numpy as np
from collections import deque
from .const import (
    WAIT_PREDICTION,
    IMU_LIST,
    IMU_FIELDS,
    PREDICTION_DONE,
    MAX_BUFFER_LEN,
    R_FOOT,
    WEIGHT_LOC,
    HEIGHT_LOC,
    ACC_ALL,
    GYR_ALL,
    GRAVITY,
)
import pickle
import os

LSTM_UNITS, FCNN_UNITS = 20, 40


class InertialNet(torch.nn.Module):
    def __init__(self, x_dim, net_name, seed=0, nlayer=1):
        super(InertialNet, self).__init__()
        self.net_name = net_name
        torch.manual_seed(seed)
        self.rnn_layer = torch.nn.LSTM(
            x_dim, LSTM_UNITS, nlayer, batch_first=True, bidirectional=True
        )
        self.dropout = torch.nn.Dropout(0.0)
        for name, param in self.rnn_layer.named_parameters():
            if "weight" in name:
                torch.nn.init.xavier_normal_(param)

    def __str__(self):
        return self.net_name

    def forward(self, sequence, lens):
        sequence = torch.nn.utils.rnn.pack_padded_sequence(
            sequence, lens, batch_first=True, enforce_sorted=False
        )
        sequence, _ = self.rnn_layer(sequence)
        sequence, _ = torch.nn.utils.rnn.pad_packed_sequence(
            sequence, batch_first=True, total_length=152
        )
        sequence = self.dropout(sequence)
        return sequence


class OutNet(torch.nn.Module):
    def __init__(self, input_dim, high_level_locs=[]):
        super(OutNet, self).__init__()
        self.high_level_locs = high_level_locs
        self.linear_1 = torch.nn.Linear(
            input_dim + len(high_level_locs), FCNN_UNITS, bias=True
        )
        self.linear_2 = torch.nn.Linear(FCNN_UNITS, 2, bias=True)
        self.relu = torch.nn.ReLU()
        for layer in [self.linear_1, self.linear_2]:
            torch.nn.init.xavier_normal_(layer.weight)

    def forward(self, sequence, others):
        if len(self.high_level_locs) > 0:
            sequence = torch.cat((sequence, others[:, :, self.high_level_locs]), dim=2)
        sequence = self.linear_1(sequence)
        sequence = self.relu(sequence)
        sequence = self.linear_2(sequence)
        weight = others[:, 0, WEIGHT_LOC].unsqueeze(1).unsqueeze(2)
        height = others[:, 0, HEIGHT_LOC].unsqueeze(1).unsqueeze(2)
        sequence = torch.div(sequence, weight * GRAVITY * height / 100)
        return sequence


class LmfImuOnlyNet(torch.nn.Module):
    """Implemented based on the paper "Efficient low-rank multimodal fusion with modality-specific factors" """

    def __init__(self, acc_dim, gyr_dim):
        super(LmfImuOnlyNet, self).__init__()
        self.acc_subnet = InertialNet(acc_dim, "acc net", seed=0)
        self.gyr_subnet = InertialNet(gyr_dim, "gyr net", seed=0)
        self.rank = 10
        self.fused_dim = 40

        self.acc_factor = torch.nn.parameter.Parameter(
            torch.Tensor(self.rank, 1, 2 * LSTM_UNITS + 1, self.fused_dim)
        )
        self.gyr_factor = torch.nn.parameter.Parameter(
            torch.Tensor(self.rank, 1, 2 * LSTM_UNITS + 1, self.fused_dim)
        )
        self.fusion_weights = torch.nn.parameter.Parameter(torch.Tensor(1, self.rank))
        self.fusion_bias = torch.nn.parameter.Parameter(torch.Tensor(1, self.fused_dim))

        # init factors
        torch.nn.init.xavier_normal_(self.acc_factor, 10)
        torch.nn.init.xavier_normal_(self.gyr_factor, 10)
        torch.nn.init.xavier_normal_(self.fusion_weights)
        self.fusion_bias.data.fill_(0)
        self.out_net = OutNet(self.fused_dim, [])  # do not use high level features

    def __str__(self):
        return "LMF IMU only net"

    def set_scalars(self, scalars):
        self.scalars = scalars

    def set_fields(self, x_fields):
        self.acc_fields = x_fields["input_acc"]
        self.gyr_fields = x_fields["input_gyr"]

    def forward(self, acc_x, gyr_x, others, lens):
        acc_x = acc_x.float()
        gyr_x = gyr_x.float()
        others = others.float()
        
        acc_h = self.acc_subnet(acc_x, lens)
        gyr_h = self.gyr_subnet(gyr_x, lens)
        batch_size = acc_h.data.shape[0]
        data_type = torch.FloatTensor

        _acc_h = torch.cat(
            (
                torch.autograd.Variable(
                    torch.ones(batch_size, acc_h.shape[1], 1).type(data_type),
                    requires_grad=False,
                ),
                acc_h,
            ),
            dim=2,
        )
        _gyr_h = torch.cat(
            (
                torch.autograd.Variable(
                    torch.ones(batch_size, gyr_h.shape[1], 1).type(data_type),
                    requires_grad=False,
                ),
                gyr_h,
            ),
            dim=2,
        )

        fusion_acc = torch.matmul(_acc_h, self.acc_factor)
        fusion_gyr = torch.matmul(_gyr_h, self.gyr_factor)
        fusion_vid = torch.full_like(fusion_acc, 1)
        fusion_zy = fusion_acc * fusion_gyr * fusion_vid
        sequence = (
            torch.matmul(self.fusion_weights, fusion_zy.permute(1, 2, 0, 3)).squeeze(
                dim=2
            )
            + self.fusion_bias
        )
        sequence = self.out_net(sequence, others)
        return sequence


class MomentPrediction:
    def __init__(self, weight, height):
        self.data_buffer = deque(maxlen=MAX_BUFFER_LEN)
        self.data_margin_before_step = 20
        self.data_margin_after_step = 20
        self.data_array_fields = [
            axis + "_" + sensor for sensor in IMU_LIST for axis in IMU_FIELDS
        ]

        base_path = os.path.abspath(os.path.dirname(__file__))
        model_state_path = os.path.join(base_path, "models", "7IMU_FUSION40_LSTM20.pth")
        
        self.model = LmfImuOnlyNet(21, 21)
   
        self.model.load_state_dict(torch.load(model_state_path, weights_only=True))
        
        self.model.eval()
        
        self.model.set_fields({"input_acc": ACC_ALL, "input_gyr": GYR_ALL})
        
        scalar_path = os.path.join(base_path, "models", "scalars.pkl")
        
        # Load the scalars and handle the clip attribute
        with open(scalar_path, "rb") as f:
            scalars = pickle.load(f)
        
        if 'input_acc' in scalars and not hasattr(scalars['input_acc'], 'clip'):
            scalars['input_acc'].clip = False
        if 'input_gyr' in scalars and not hasattr(scalars['input_gyr'], 'clip'):
            scalars['input_gyr'].clip = False

        self.model.set_scalars(scalars)
        
        self.model.acc_col_loc = [
            self.data_array_fields.index(field) for field in self.model.acc_fields
        ]
        self.model.gyr_col_loc = [
            self.data_array_fields.index(field) for field in self.model.gyr_fields
        ]


        self.weight = weight
        self.height = height

        anthro_data = np.zeros([1, 152, 2], dtype=float)
        anthro_data[:, :, WEIGHT_LOC] = self.weight
        anthro_data[:, :, HEIGHT_LOC] = self.height
        self.model_inputs = {
            "others": torch.from_numpy(anthro_data),
            "step_length": None,
            "input_acc": None,
            "input_gyr": None,
        }

    def update_stream(self, data, gait_phase):
        self.data_buffer.append([data, 0.0, 0.0, 0])
        package = data[R_FOOT]["Package"]
        if gait_phase.current_phase == WAIT_PREDICTION:
            if package - gait_phase.off_package >= self.data_margin_after_step - 1:
                step_length = int(
                    gait_phase.off_package
                    - gait_phase.strike_package
                    + self.data_margin_before_step
                    + self.data_margin_after_step
                )
                if step_length <= len(self.data_buffer):
                    # start = time.time()
                    inputs = self.transform_input(
                        step_length, self.data_buffer, self.model_inputs
                    )
                    pred = self.model(
                        inputs["input_acc"],
                        inputs["input_gyr"],
                        inputs["others"],
                        inputs["step_length"],
                    )
                    pred = pred.detach().numpy().astype(float)[0]
                    for i_sample in range(step_length):
                        self.data_buffer[-step_length + i_sample][1:3] = [
                            pred[i_sample, 0],
                            pred[i_sample, 1],
                        ]
                    for i_sample in range(
                        self.data_margin_before_step,
                        step_length - self.data_margin_after_step,
                    ):
                        self.data_buffer[-step_length + i_sample][3] = 1
                    # duration = time.time() - start
                    # print(duration)

                gait_phase.current_phase = PREDICTION_DONE
        if len(self.data_buffer) == MAX_BUFFER_LEN:
            return [self.data_buffer.popleft()]
        return []

    def transform_input(self, step_length, data_buffer, model_inputs):
        raw_data = []
        for sample_data in list(data_buffer)[-step_length:]:
            raw_data_one_row = []
            for i_sensor in range(len(IMU_LIST)):
                raw_data_one_row.extend(
                    [sample_data[0][i_sensor][field] for field in IMU_FIELDS]
                )
            raw_data.append(raw_data_one_row)
        data = np.array(raw_data, dtype=float)
        data[:, self.model.acc_col_loc] = self.normalize_array_separately(
            data[:, self.model.acc_col_loc],
            self.model.scalars["input_acc"],
            "transform",
        )
        model_inputs["input_acc"] = torch.from_numpy(
            np.expand_dims(data[:, self.model.acc_col_loc], axis=0)
        )
        data[:, self.model.gyr_col_loc] = self.normalize_array_separately(
            data[:, self.model.gyr_col_loc],
            self.model.scalars["input_gyr"],
            "transform",
        )
        model_inputs["input_gyr"] = torch.from_numpy(
            np.expand_dims(data[:, self.model.gyr_col_loc], axis=0)
        )

        model_inputs["step_length"] = torch.tensor([step_length], dtype=torch.int32)
        return model_inputs

    @staticmethod
    def normalize_array_separately(data, scalar, method, scalar_mode="by_each_column"):
        input_data = data.copy()
        original_shape = input_data.shape
        target_shape = (
            [-1, input_data.shape[1]] if scalar_mode == "by_each_column" else [-1, 1]
        )
        input_data = input_data.reshape(target_shape)
        scaled_data = getattr(scalar, method)(input_data)
        scaled_data = scaled_data.reshape(original_shape)
        return scaled_data
