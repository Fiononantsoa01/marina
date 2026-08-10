# ---- Étape 1 : build ----
FROM ocaml/opam:debian-12-ocaml-4.14 AS build

WORKDIR /home/opam/marina

# On copie les sources du projet
COPY --chown=opam:opam . .

# make utilise ocamlc + str.cma, tous deux déjà présents dans l'image ocaml/opam
RUN opam exec -- make clean || true \
 && opam exec -- make

# ---- Étape 2 : image finale ----
FROM debian:12-slim

WORKDIR /app

# python3 (bibliothèque standard uniquement) sert juste à exposer le binaire
# CLI via une petite API HTTP - aucun paquet pip n'est requis.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*

# Le binaire est produit avec -custom (runtime OCaml statiquement lié),
# donc aucune dépendance OCaml n'est nécessaire à l'exécution.
COPY --from=build /home/opam/marina/marina /app/marina
COPY server.py /app/server.py

ENV PORT=8080
EXPOSE 8080

CMD ["python3", "/app/server.py"]
