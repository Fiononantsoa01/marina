FROM ocaml/opam:debian-12-ocaml-4.14

USER root
WORKDIR /app

# Copie avec les bons droits (l'image utilise l'utilisateur opam)
COPY --chown=opam:opam . .

USER opam

# ocamlfind est nécessaire, ounit2 ne l'est pas pour le binaire
RUN opam install -y ocamlfind

# Compile
RUN eval $(opam env) && make

# On met le binaire dans un endroit propre
USER root
RUN cp /app/marina /usr/local/bin/marina && \
    chmod +x /usr/local/bin/marina

USER opam

# Par défaut on lance le binaire
ENTRYPOINT ["marina"]