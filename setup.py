from setuptools import setup, find_packages

setup(
    name='pdf-locher',
    version='1.0.0',
    author='Digitaldruide',
    author_email='nirvana@digitaldrui.de',
    description='hole punches your pdfs',
    packages=find_packages(),
    py_modules=["pdf_locher"],
    install_requires=[
        'charset-normalizer==3.4.4',
        'numpy==2.4.0',
        'pdf2image==1.17.0',
        'pillow==12.0.0',
        'PyPDF2==3.0.1',
        'reportlab==4.4.7',
    ],
    entry_points={
        'console_scripts': [
            'pdf-locher=pdf_locher:main', 
        ],
    },
)
