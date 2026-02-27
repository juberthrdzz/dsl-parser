# Carrusel hospitalario
CARRUSEL farmacia_central {
  ESPACIOS: 48
  CAPACIDAD: 80

  PRODUCTO paracetamol_500 {
    PRECIO: 25.50
    MINIMO: 30
    MAXIMO: 200
    CRITICIDAD: ALTA
  }

  PRODUCTO venda_elastica {
    PRECIO: 18.00
    MINIMO: 20
    MAXIMO: 120
    CRITICIDAD: MEDIA
  }
}

SIMULAR {
  TRANSACCIONES: [
    RETIRAR(paracetamol_500, 10),
    RETIRAR(venda_elastica, 5),
    RESURTIR(paracetamol_500, 40),
    CONTAR(paracetamol_500)
  ]

  ESTADO
  ESTADISTICAS
  REPORTE("reporte_farmacia_central")
}
