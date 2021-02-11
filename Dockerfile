FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# increment to rerun Dockerfile on system
RUN echo 'hi 1'

RUN apt-get update
ENV PYTHONUNBUFFERED=True

RUN apt-get install --yes vim

WORKDIR /opt

# TODO pin this? rn changes with latest release
RUN curl --location https://sourceforge.net/projects/rdp-classifier/files/latest/download > rdp_classifier.zip && \
unzip rdp_classifier.zip && \
rm rdp_classifier.zip

RUN pip install pandas dotmap plotly
RUN pip install pipenv coverage pytest-cov python-coveralls flake8 
RUN pip install plotly==4.14.3 kaleido

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
