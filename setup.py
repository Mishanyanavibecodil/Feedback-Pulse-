"""
Настройка установки проекта Feedback Pulse.

Этот модуль содержит конфигурацию для установки проекта через pip.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="feedback-pulse",
    version="1.0.0",
    author="Mishanyanavibecodil",
    author_email="your.email@example.com",
    description="Система для сбора и анализа отзывов с Google Maps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mishanyanavibecodil/Feedback-Pulse-",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "selenium>=4.10.0",
        "webdriver-manager>=4.0.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "python-telegram-bot>=20.0",
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "nltk>=3.8.0",
        "psutil>=5.9.0",
        "python-dotenv>=1.0.0",
        "cryptography>=41.0.0",
        "pydantic>=2.0.0",
        "aiohttp>=3.8.0",
        "asyncio>=3.4.0",
        "tqdm>=4.65.0",
        "colorama>=0.4.6",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "feedback-pulse=src.main:main",
        ],
    },
    package_data={
        "feedback_pulse": [
            "config/*.json",
            "models/*.bin",
            "data/*.csv",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 