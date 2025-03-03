import itertools
import unittest

from ray.rllib.core.models.base import ENCODER_OUT, STATE_OUT
from ray.rllib.core.models.configs import LSTMEncoderConfig
from ray.rllib.utils.test_utils import framework_iterator, ModelChecker


class TestRecurrentEncoders(unittest.TestCase):
    def test_lstm_encoders(self):
        """Tests building LSTM encoders properly and checks for correct architecture."""

        # Loop through different combinations of hyperparameters.
        inputs_dimss = [[1], [100]]
        output_dimss = [[1], [100]]
        num_lstm_layerss = [1, 3]
        hidden_dims = [16, 128]
        output_activations = [None, "linear", "relu"]
        use_biases = [False, True]

        for permutation in itertools.product(
            inputs_dimss,
            num_lstm_layerss,
            hidden_dims,
            output_activations,
            output_dimss,
            use_biases,
        ):
            (
                inputs_dims,
                num_lstm_layers,
                hidden_dim,
                output_activation,
                output_dims,
                use_bias,
            ) = permutation

            print(
                f"Testing ...\n"
                f"input_dims: {inputs_dims}\n"
                f"num_lstm_layers: {num_lstm_layers}\n"
                f"hidden_dim: {hidden_dim}\n"
                f"output_activation: {output_activation}\n"
                f"output_dims: {output_dims}\n"
                f"use_bias: {use_bias}\n"
            )

            config = LSTMEncoderConfig(
                input_dims=inputs_dims,
                num_lstm_layers=num_lstm_layers,
                hidden_dim=hidden_dim,
                output_dims=output_dims,
                output_activation=output_activation,
                use_bias=use_bias,
            )

            # Use a ModelChecker to compare all added models (different frameworks)
            # with each other.
            model_checker = ModelChecker(config)

            for fw in framework_iterator(frameworks=("tf2", "torch")):
                # Add this framework version of the model to our checker.
                outputs = model_checker.add(framework=fw)
                # Output shape: [1=B, 1=T, [output_dim]]
                self.assertEqual(outputs[ENCODER_OUT].shape, (1, 1, output_dims[0]))
                # State shapes: [1=B, 1=num_layers, [hidden_dim]]
                self.assertEqual(
                    outputs[STATE_OUT]["h"].shape,
                    (1, num_lstm_layers, hidden_dim),
                )
                self.assertEqual(
                    outputs[STATE_OUT]["c"].shape,
                    (1, num_lstm_layers, hidden_dim),
                )

            # Check all added models against each other (only if bias=False).
            # See here on why pytorch uses two bias vectors per layer and tf only uses
            # one:
            # https://towardsdatascience.com/implementation-differences-in-lstm-
            # layers-tensorflow-vs-pytorch-77a31d742f74
            if use_bias is False:
                model_checker.check()


if __name__ == "__main__":
    import pytest
    import sys

    sys.exit(pytest.main(["-v", __file__]))
