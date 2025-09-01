from setuptools import setup, find_packages

# A minimalist setup file to make the project installable and define its dependencies.
# Running `pip install .` in the root directory will install the package and its requirements.

setup(
    name="encrypted_udp_jpeg_stream",
    version="0.1.0",
    author="Mert KUREŞ",
    author_email="mertkures@hotmail.com",
    description="A modular package to securely stream compressed camera footage over a network.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    install_requires=[
        "opencv-python",  # For camera access and image manipulation
        "numpy",          # Dependency for OpenCV, used for image data arrays
        "cryptography",   # For robust, high-level encryption
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Networking",
        "Topic :: Multimedia :: Video :: Capture",
        "Topic :: Security :: Cryptography",
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'stream-camera=streamer.main:main',
            'generate-stream-key=streamer.security:generate_key_and_save',
        ],
    },
)

