# Copyright 2018 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Functions that mutate inputs for coverage guided fuzzing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import numpy as np


# pylint: disable=too-many-locals
def do_basic_mutations(
    corpus_element, mutations_count, constraint=None, a_min=-1.0, a_max=1.0
):
    """Mutates image inputs with white noise. PS: what is white noise?

  Args:
    corpus_element: A CorpusElement object. It's assumed in this case that
      corpus_element.data[0] is a numpy representation of an image and
      corput_element.data[1] is a label or something we *don't* want to change.
    mutations_count: Integer representing number of mutations to do in
      parallel.
    constraint: If not None, a constraint on the norm of the total mutation.
    a_max: pixels max, if not for image then can change
    a_min: pixels min, if not for image the can change

  Returns:
    A list of batches, the first of which is mutated images and the second of
    which is passed through the function unchanged (because they are image
    labels or something that we never intended to mutate).
  """
    # Here we assume the corpus.data is of the form (image, label)
    # We never mutate the label.
    if len(corpus_element.data) > 1:
        image, label = corpus_element.data  # image: (28, 28, 1)
        image_batch = np.tile(image, [mutations_count, 1, 1, 1])  # image_batch: (100, 28, 28, 1)
    else:
        image = corpus_element.data[0]
        image_batch = np.tile(image, [mutations_count] + list(image.shape))

    # noise is add some random number? and sigma why set 0.2
    sigma = 0.2
    noise = np.random.normal(size=image_batch.shape, scale=sigma)  # Gaussian Distribution
    # noise = np.random.laplace(size=image_batch.shape, scale=sigma)
    # noise = np.random.logistic(size=image_batch.shape, scale=sigma)

    if constraint is not None:  # mutation trick 2
        # (image - original_image) is a single image. it gets broadcast into a batch
        # when added to 'noise'
        ancestor, _ = corpus_element.oldest_ancestor()  # least ancestor: parent
        original_image = ancestor.data[0]

        original_image_batch = np.tile(original_image, [mutations_count, 1, 1, 1])

        cumulative_noise = noise + (image_batch - original_image_batch)  # connect with ancestor image
        # pylint: disable=invalid-unary-operand-type
        noise = np.clip(cumulative_noise, a_min=-constraint, a_max=constraint)
        mutated_image_batch = noise + original_image_batch
    else:
        mutated_image_batch = noise + image_batch  # mutation trick 1

    mutated_image_batch = np.clip(mutated_image_batch, a_min=a_min, a_max=a_max)

    if len(corpus_element.data) > 1:
        label_batch = np.tile(label, [mutations_count])
        mutated_batches = [mutated_image_batch, label_batch]
    else:
        mutated_batches = [mutated_image_batch]
    return mutated_batches
