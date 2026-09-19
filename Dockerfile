# Build the engine's reader, refuse to publish if any edition fails its check, export the static site, serve it.
FROM node:24-alpine AS reader
RUN apk add --no-cache git
ARG ENGINE_REF=88b687a
RUN git clone -q https://github.com/vaelkeep/vael-paper.git /engine && git -C /engine checkout -q $ENGINE_REF
WORKDIR /engine/reader
RUN npm ci --silent && npm run build

FROM python:3.13-slim AS site
COPY --from=reader /engine /engine
RUN pip install -q --no-cache-dir /engine/server
WORKDIR /paper
COPY editions/ editions/
# Never publish on red: the build fails if any edition has a mark.
RUN vael-paper-check --root editions --all > /dev/null
RUN vael-paper-export --editions editions --reader /engine/reader/dist --out site \
      --base-url https://aberdeen-daily.technoir.cloud/ \
      --og-description "Aberdeen's local news every morning: original stories from public reporting, every source credited, weather and markets computed by code."
COPY web/ site/

FROM nginx:1.27-alpine
COPY --from=site /paper/site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
