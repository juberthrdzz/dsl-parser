CARRUSEL farmacia_error_lexico {
  ESPACIOS: 10
  CAPACIDAD: 10

  PRODUCTO ibuprofeno {
    PRECIO: $25.50
    MINIMO: 1
    MAXIMO: 20
    CRITICIDAD: MEDIA
  }
}

SIMULAR {
  TRANSACCIONES: [ CONTAR(ibuprofeno) ]
  ESTADO
}
