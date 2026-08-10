
FROM ocaml/opam:debian-12-ocaml-4.14 AS build

WORKDIR /home/opam/marina

COPY --chown=opam:opam . .


RUN opam exec -- make clean || true \
 && opam exec -- make

FROM debian:12-slim

WORKDIR /app


RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=build /home/opam/marina/marina /app/marina
COPY server.py /app/server.py

ENV PORT=8080
EXPOSE 8080

CMD ["python3", "/app/server.py"]
