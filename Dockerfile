FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
RUN apt-get update
ENV PYTHONUNBUFFERED=True

RUN apt-get install --yes vim

WORKDIR /opt

RUN curl --insecure --location https://sourceforge.net/projects/rdp-classifier/files/rdp-classifier/rdp_classifier_2.13.zip/download > rdp_classifier.zip && \
unzip rdp_classifier.zip && \
rm rdp_classifier.zip

RUN pip install --upgrade pip
RUN pip install \
    pandas dotmap plotly==4.14.3 \
    pipenv coverage pytest-cov python-coveralls flake8 

# parameters from training RDP Clsf on SILVA
# are on Google Drive
RUN pip install gdown
RUN mkdir /refdata && \
cd /refdata && \
gdown https://drive.google.com/uc?id=15tdT7_hJV8lOCpLX1-IfKw7w1IwKn21Z 
RUN cd /refdata && tar xzf /refdata/refdata.tgz    

# -----------------------------------------
COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module


RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
