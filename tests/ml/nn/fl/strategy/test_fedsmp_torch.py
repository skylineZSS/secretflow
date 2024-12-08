# Copyright 2024 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import torch.optim as optim
from torch import nn
from torch.nn import functional as F
from torchmetrics import Accuracy, Precision

import secretflow as sf
from examples.security.h_gia.FedSMP_defense.FedSMP_torch import FedSMPServerCallback
from secretflow import reveal
from secretflow.security import SecureAggregator
from secretflow_fl.ml.nn import FLModel
from secretflow_fl.ml.nn.core.torch import (
    BaseModule,
    TorchModel,
    metric_wrapper,
    optim_wrapper,
)
from secretflow_fl.utils.simulation.datasets_fl import load_mnist


# the global model
class FLBaseNet(BaseModule):
    def __init__(self, classes=10):
        super(FLBaseNet, self).__init__()
        self.act = nn.ReLU()
        self.body = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            self.act,
            nn.AvgPool2d(kernel_size=2, stride=2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            self.act,
            nn.AvgPool2d(kernel_size=2, stride=2),
        )
        self.fc1 = nn.Linear(3136, 100)
        self.fc2 = nn.Linear(100, classes)

    def forward(self, x):
        x = self.body(x)
        x = x.view(x.shape[0], -1)
        x = self.act(self.fc1(x))
        return self.fc2(x)


def do_test_fedsmp(configs: dict, alice, bob, carol):

    # prepare dataset
    (_, _), (data, label) = load_mnist(
        parts={
            alice: 0.4,
            bob: 0.6,
        },
        normalized_x=True,
        categorical_y=True,
        is_torch=True,
    )

    loss_fn = nn.CrossEntropyLoss

    optim_fn = optim_wrapper(optim.Adam, lr=configs['train_lr'])

    model_def = TorchModel(
        model_fn=FLBaseNet,
        loss_fn=loss_fn,
        optim_fn=optim_fn,
        metrics=[
            metric_wrapper(
                Accuracy, task="multiclass", num_classes=10, average='micro'
            ),
            metric_wrapper(
                Precision, task="multiclass", num_classes=10, average='micro'
            ),
        ],
    )

    device_list = [alice, bob]
    server = carol
    aggregator = SecureAggregator(server, device_list)

    # spcify params
    fl_model = FLModel(
        server=server,
        device_list=device_list,
        model=model_def,
        aggregator=aggregator,
        strategy='fed_smp',
        backend="torch",
        noise_multiplier=configs['noise_multiplier'],
        l2_norm_clip=configs['l2_norm_clip'],
        num_clients=len(device_list),
    )

    # realize the operations in the server side with callback
    fedsmp_server_callback = FedSMPServerCallback(
        server=carol,
        compression_ratio=configs['compression_ratio'],
        global_net=FLBaseNet(),
    )

    history = fl_model.fit(
        data,
        label,
        epochs=10,
        batch_size=32,
        aggregate_freq=1,
        callbacks=[fedsmp_server_callback],
    )

    return


# configurations
configs = {
    "batchsize": 32,
    "epochs": 10,
    "train_lr": 0.004,
    "noise_multiplier": 0.04,
    "l2_norm_clip": 1.0,
    "compression_ratio": 0.6,
}


def test_fedsmp(sf_simulation_setup_devices):
    alice = sf_simulation_setup_devices.alice
    bob = sf_simulation_setup_devices.bob
    carol = sf_simulation_setup_devices.carol
    do_test_fedsmp(configs, alice, bob, carol)


# sf.init(['alice', 'bob', 'carol'], address='local', debug_mode=True)
# alice, bob, carol = sf.PYU('alice'), sf.PYU('bob'), sf.PYU('carol')
# do_test_fedsmp(configs, alice, bob, carol)