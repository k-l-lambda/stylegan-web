
"""Minimal script for generating an image using pre-trained StyleGAN generator."""

import os
import pickle
import numpy as np
import PIL.Image
import dnnlib
import dnnlib.tflib as tflib
import config
import time

def main():
    t0 = time.time()
    print('t0:', t0)

    # Initialize TensorFlow.
    tflib.init_tf()     # 1.46s

    print('t1:', time.time() - t0)

    # Load pre-trained network.
    #url = 'https://drive.google.com/uc?id=1MEGjdvVpUsu1jB4zrXZN7Y4kBBOzizDQ' # karras2019stylegan-ffhq-1024x1024.pkl
    url = 'http://127.0.0.1:8081/Visual%20Studio%202015/Projects/stylegan/karras2019stylegan-ffhq-1024x1024.pkl'
    with dnnlib.util.open_url(url, cache_dir=config.cache_dir) as f:
        #print('f:', f)
        print('t2:', time.time() - t0)

        _G, _D, Gs = pickle.load(f)     # 6.8s
        # _G = Instantaneous snapshot of the generator. Mainly useful for resuming a previous training run.
        # _D = Instantaneous snapshot of the discriminator. Mainly useful for resuming a previous training run.
        # Gs = Long-term average of the generator. Yields higher-quality results than the instantaneous snapshot.

        print('t3:', time.time() - t0)

    # Print network details.
    #Gs.print_layers()       # 0.13s

    print('t4:', time.time() - t0)

    # Pick latent vector.
    rnd = np.random.RandomState(4)
    latents = rnd.randn(1, Gs.input_shape[1])

    print('t5:', time.time() - t0)

    print('input_shape:', Gs.input_shape)
    #print('latents:', latents)

    # Generate image.
    fmt = dict(func=tflib.convert_images_to_uint8, nchw_to_nhwc=True)       # 0.016s
    print('t6:', time.time() - t0)
    images = Gs.run(latents, None, truncation_psi=-0.5, randomize_noise=True, output_transform=fmt)     # 4.96s

    print('images:', images)

    print('t7:', time.time() - t0)

    # Save image.
    os.makedirs(config.result_dir, exist_ok=True)
    png_filename = os.path.join(config.result_dir, 'example.png')
    PIL.Image.fromarray(images[0], 'RGB').save(png_filename)        # 0.32s

    print('t8:', time.time() - t0)

if __name__ == "__main__":
    main()
