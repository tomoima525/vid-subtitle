from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="vid-subtitle",
    version="0.1.0",
    author="Tomo",
    author_email="tomoima525@gmail.com",
    description="A Python library to add subtitles to videos using FFmpeg and OpenAI Whisper API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomoima525/vid-subtitle",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vid-subtitle=vid_subtitle.cli:main",
        ],
    },
)
