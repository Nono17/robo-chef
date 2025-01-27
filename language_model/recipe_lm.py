
# This code is recycled from the PTB Language Model tutorial for TensorFlow. The
# original copyright can be found below.

# ==============================================================================
# Copyright 2015 Google Inc. All Rights Reserved.
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
# ==============================================================================

"""

Trains the model described in:
(Zaremba, et. al.) Recurrent Neural Network Regularization
http://arxiv.org/abs/1409.2329

The data required for this example is in the data/ dir of the
PTB dataset from Tomas Mikolov's webpage:

http://www.fit.vutbr.cz/~imikolov/rnnlm/simple-examples.tgz

There are 3 supported model configurations:
===========================================
| config | epochs | train | valid  | test
===========================================
| small  | 13     | 37.99 | 121.39 | 115.91
| medium | 39     | 48.45 |  86.16 |  82.07
| large  | 55     | 37.87 |  82.62 |  78.29
The exact results may vary depending on the random initialization.

The hyperparameters used in the model:
- init_scale - the initial scale of the weights
- learning_rate - the initial value of the learning rate
- max_grad_norm - the maximum permissible norm of the gradient
- num_layers - the number of LSTM layers
- num_steps - the number of unrolled steps of LSTM
- hidden_size - the number of LSTM units
- max_epoch - the number of epochs trained with the initial learning rate
- max_max_epoch - the total number of epochs for training
- keep_prob - the probability of keeping weights in the dropout layer
- lr_decay - the decay of the learning rate for each epoch after "max_epoch"
- batch_size - the batch size

To train:
  python recipe_lm.py \
    --data_path=< path to directory with lm.train.txt and lm.valid.txt > \
    --model_path=< file in which to save trained parameters > \
    --train 1

To score test file:
  python recipe_lm.py \
    --data_path=< path to directory with lm.train.txt and lm.valid.txt > \
    --model_path=< file from which to restore trained parameters > \
    --notrain \
    --review_segments_path=< file of segments to score >

"""
from __future__ import absolute_import
from __future__ import print_function

import time

import tensorflow.python.platform

import numpy as np
import tensorflow as tf

from tensorflow.models.rnn import rnn
from tensorflow.models.rnn import rnn_cell
from tensorflow.models.rnn import seq2seq
import reader

flags = tf.flags

flags.DEFINE_string(
    "model", "small",
    "A type of model. Possible options are: small, medium, large.")
flags.DEFINE_string("data_path", None, "data_path")
flags.DEFINE_string("model_path", None, "model_path")
flags.DEFINE_string('review_segments_path', None, 'review_segments_path')
flags.DEFINE_boolean("train", True, "whether to train the model (or reuse pre-trained parameters)")

FLAGS = flags.FLAGS


class LangModel(object):
  """The language model."""

  def __init__(self, is_training, config):
    self.batch_size = batch_size = config.batch_size
    self.num_steps = num_steps = config.num_steps
    size = config.hidden_size
    vocab_size = config.vocab_size

    self._input_data = tf.placeholder(tf.int32, [batch_size, num_steps])
    self._targets = tf.placeholder(tf.int32, [batch_size, num_steps])

    # Slightly better results can be obtained with forget gate biases
    # initialized to 1 but the hyperparameters of the model would need to be
    # different than reported in the paper.
    lstm_cell = rnn_cell.BasicLSTMCell(size, forget_bias=0.0)
    if is_training and config.keep_prob < 1:
      lstm_cell = rnn_cell.DropoutWrapper(
          lstm_cell, output_keep_prob=config.keep_prob)
    cell = rnn_cell.MultiRNNCell([lstm_cell] * config.num_layers)

    self._initial_state = cell.zero_state(batch_size, tf.float32)

    with tf.device("/cpu:0"):
      embedding = tf.get_variable("embedding", [vocab_size, size])
      inputs = tf.split(
          1, num_steps, tf.nn.embedding_lookup(embedding, self._input_data))
      inputs = [tf.squeeze(input_, [1]) for input_ in inputs]

    if is_training and config.keep_prob < 1:
      inputs = [tf.nn.dropout(input_, config.keep_prob) for input_ in inputs]

    # Simplified version of tensorflow.models.rnn.rnn.py's rnn().
    # This builds an unrolled LSTM for tutorial purposes only.
    # In general, use the rnn() or state_saving_rnn() from rnn.py.
    #
    # The alternative version of the code below is:
    #
    outputs, states = rnn.rnn(cell, inputs, initial_state=self._initial_state)

    output = tf.reshape(tf.concat(1, outputs), [-1, size])
    logits = tf.nn.xw_plus_b(output,
                             tf.get_variable("softmax_w", [size, vocab_size]),
                             tf.get_variable("softmax_b", [vocab_size]))

    print('logits shape: {0}'.format(logits.get_shape()))

    targets__ = tf.reshape(self._targets, [-1])
    print('targets shape: {0}'.format(targets__.get_shape()))

    print('weights shape: {0}'.format(tf.ones([batch_size * num_steps]).get_shape()))


    loss = seq2seq.sequence_loss_by_example([logits],
                                            [targets__],
                                            [tf.ones([batch_size * num_steps])],
                                            vocab_size)
    self._cost = cost = tf.reduce_sum(loss) / batch_size
    self._final_state = states[-1]

    print('cost shape: {0}'.format(cost.get_shape()))

    if not is_training:
      return

    self._lr = tf.Variable(0.0, trainable=False)
    tvars = tf.trainable_variables()
    grads, _ = tf.clip_by_global_norm(tf.gradients(cost, tvars),
                                      config.max_grad_norm)
    optimizer = tf.train.GradientDescentOptimizer(self.lr)
    self._train_op = optimizer.apply_gradients(zip(grads, tvars))

  def assign_lr(self, session, lr_value):
    session.run(tf.assign(self.lr, lr_value))

  @property
  def input_data(self):
    return self._input_data

  @property
  def targets(self):
    return self._targets

  @property
  def initial_state(self):
    return self._initial_state

  @property
  def cost(self):
    return self._cost

  @property
  def final_state(self):
    return self._final_state

  @property
  def lr(self):
    return self._lr

  @property
  def train_op(self):
    return self._train_op


class SmallConfig(object):
  """Small config."""
  init_scale = 0.1
  learning_rate = 1.0
  max_grad_norm = 5
  num_layers = 2
  num_steps = 20
  hidden_size = 200
  max_epoch = 4
  max_max_epoch = 8
  keep_prob = 1.0
  lr_decay = 0.5
  batch_size = 20

  def __init__(self, n=10000):
    self.vocab_size = n

class MediumConfig(object):
  """Medium config."""
  init_scale = 0.05
  learning_rate = 1.0
  max_grad_norm = 5
  num_layers = 2
  num_steps = 35
  hidden_size = 650
  max_epoch = 6
  max_max_epoch = 39
  keep_prob = 0.5
  lr_decay = 0.8
  batch_size = 20

  def __init__(self, n=10000):
    self.vocab_size = n

class LargeConfig(object):
  """Large config."""
  init_scale = 0.04
  learning_rate = 1.0
  max_grad_norm = 10
  num_layers = 2
  num_steps = 35
  hidden_size = 1500
  max_epoch = 14
  max_max_epoch = 55
  keep_prob = 0.35
  lr_decay = 1 / 1.15
  batch_size = 20

  def __init__(self, n=10000):
    self.vocab_size = n


def run_epoch(session, m, data, eval_op, verbose=False):
  """Runs the model on the given data."""
  if len(data) <= 1:
    return np.inf

  epoch_size = ((len(data) // m.batch_size) - 1) // m.num_steps
  start_time = time.time()
  costs = 0.0
  iters = 0
  state = m.initial_state.eval()
  for step, (x, y) in enumerate(reader.data_iterator(data, m.batch_size,
                                                    m.num_steps)):
    cost, state, _ = session.run([m.cost, m.final_state, eval_op],
                                 {m.input_data: x,
                                  m.targets: y,
                                  m.initial_state: state})
    costs += cost
    iters += m.num_steps

    if verbose and step % (epoch_size // 10) == 10:
      print("%.3f perplexity: %.3f speed: %.0f wps" %
            (step * 1.0 / epoch_size, np.exp(costs / iters),
             iters * m.batch_size / (time.time() - start_time)))

  return np.exp(costs / iters)


def get_config(vocab_size, model_size):
  if model_size == "small":
    return SmallConfig(vocab_size)
  elif model_size == "medium":
    return MediumConfig(vocab_size)
  elif model_size == "large":
    return LargeConfig(vocab_size)
  else:
    raise ValueError("Invalid model: %s", model_size)

def train_model(data_path, model_path, model_size):
  raw_data = reader.get_raw_training_data(data_path)
  train_data, valid_data, vocab_size, word_to_id = raw_data

  config = get_config(vocab_size, model_size)

  with tf.Graph().as_default(), tf.Session() as session:
    initializer = tf.random_uniform_initializer(-config.init_scale,
                                                config.init_scale)
    with tf.variable_scope("model", reuse=None, initializer=initializer):
      m = LangModel(is_training=True, config=config)
    with tf.variable_scope("model", reuse=True, initializer=initializer):
      mvalid = LangModel(is_training=False, config=config)

    tf.initialize_all_variables().run()

    # Add ops to save and restore all the variables.
    saver = tf.train.Saver()

    for i in range(config.max_max_epoch):
      lr_decay = config.lr_decay ** max(i - config.max_epoch, 0.0)
      m.assign_lr(session, config.learning_rate * lr_decay)

      print("Epoch: %d Learning rate: %.3f" % (i + 1, session.run(m.lr)))
      train_perplexity = run_epoch(session, m, train_data, m.train_op,
                                   verbose=True)
      print("Epoch: %d Train Perplexity: %.3f" % (i + 1, train_perplexity))
      valid_perplexity = run_epoch(session, mvalid, valid_data, tf.no_op())
      print("Epoch: %d Valid Perplexity: %.3f" % (i + 1, valid_perplexity))

    # Save the variables to disk.
    save_path = saver.save(session, model_path)
    print("Model saved in file: {0}".format(save_path))

def scoreData(review_segments, data_path, model_path, model_size, verbose=False):
  raw_data = reader.get_raw_training_data(data_path)
  train_data, valid_data, vocab_size, word_to_id = raw_data

  segments_data = reader.process_review_segments(review_segments, word_to_id)
  segments_scores = []

  eval_config = get_config(vocab_size, model_size)
  eval_config.batch_size = 1
  eval_config.num_steps = 1

  with tf.Graph().as_default(), tf.Session() as session:
    initializer = tf.random_uniform_initializer(-eval_config.init_scale,
                                                eval_config.init_scale)
    with tf.variable_scope("model", initializer=initializer):
      model = LangModel(is_training=False, config=eval_config)

    tf.initialize_all_variables().run()

    # Add ops to save and restore all the variables.
    saver = tf.train.Saver()

    # Restore variables from disk.
    saver.restore(session, model_path)
    print("Model restored from saved parameters at {0}".format(model_path))


    # Score the review segments
    for segment in segments_data:
      loglikelihood = -np.log(run_epoch(session, model, segment, tf.no_op()))
      segments_scores.append(loglikelihood)
      if verbose:
        print("Test Avg Loglikelihood: %.3f" % loglikelihood)

  return segments_scores


def main(unused_args):
  if not FLAGS.data_path:
    raise ValueError("Must set --data_path to training data directory")
  if not FLAGS.model_path:
    raise ValueError("Must set --model_path to an output file")

  if FLAGS.train:
    print('==> Training model')
    train_model(FLAGS.data_path, FLAGS.model_path, FLAGS.model)


  if FLAGS.review_segments_path is not None:
    print('==> Evaluating model on review segments')
    with tensorflow.python.platform.gfile.GFile(FLAGS.review_segments_path, "r") as f:
      review_segments = f.readlines()
      scoreData(review_segments, FLAGS.data_path, FLAGS.model_path, FLAGS.model, verbose=True)


if __name__ == "__main__":
  tf.app.run()
