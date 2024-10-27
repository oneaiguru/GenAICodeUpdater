# setup.py
from setuptools import setup, find_packages

setup(
    name="llmcodeupdater",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typing",
    ],
    python_requires=">=3.7",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for updating code using LLM outputs",
    keywords="llm, code, update",
)
