CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    cpf VARCHAR(11),
    nome VARCHAR(255),
    subtipo VARCHAR(255) NOT NULL
);

CREATE TABLE funcionario (
    usuario_id INTEGER NOT NULL PRIMARY KEY,
    tipo VARCHAR(255) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);
