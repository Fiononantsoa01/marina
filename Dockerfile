FROM ocaml/opam:debian-12-ocaml-4.14

WORKDIR /app

COPY . .

RUN opam install -y ocamlfind ounit2

RUN eval $(opam env) && make

ENTRYPOINT ["/app/marina"]