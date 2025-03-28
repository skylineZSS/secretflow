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

import pytest

from secretflow.security.aggregation.plain_aggregator import PlainAggregator
from secretflow_fl.security.aggregation.sparse_plain_aggregator import (
    SparsePlainAggregator,
)
from tests.security.aggregation.test_aggregator_base import AggregatorBase


class TestPlainAggregator(AggregatorBase):
    @pytest.fixture()
    def env_and_aggregator(self, sf_production_setup_devices_ray):
        yield sf_production_setup_devices_ray, PlainAggregator(
            sf_production_setup_devices_ray.carol
        )


class TestSparsePlainAggregator(AggregatorBase):
    @pytest.fixture()
    def env_and_aggregator(self, sf_production_setup_devices_ray):
        yield sf_production_setup_devices_ray, SparsePlainAggregator(
            sf_production_setup_devices_ray.carol
        )
