FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.
RUN echo hi

RUN apt-get update
ENV PYTHONUNBUFFERED=True

RUN apt-get install --yes vim

WORKDIR /opt

RUN curl --location https://sourceforge.net/projects/rdp-classifier/files/latest/download > rdp_classifier.zip && \
unzip rdp_classifier.zip && \
rm rdp_classifier.zip

RUN pip install pandas dotmap plotly

RUN apt-get install --yes gcc
RUN apt-get install --yes libgtk2.0-0
RUN apt-get install --yes xvfb
RUN pip install --upgrade pip
RUN pip install psutil requests
RUN conda install --yes --channel plotly plotly-orca
RUN apt-get install --yes libgtk-3-0 libxss1 libasound2
# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
