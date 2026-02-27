CARRUSEL farmacia_error_sintaxis {
  ESPACIOS: 10
  CAPACIDAD: 10

  PRODUCTO amoxicilina {
    PRECIO: 80.00
    MINIMO: 5
    MAXIMO: 50
    CRITICIDAD: ALTA
  }
}

SIMULAR {
  TRANSACCIONES: [
    RETIRAR(amoxicilina, 1)
  ESTADO
}
