CARRUSEL urgencias {
  ESPACIOS: 12;
  CAPACIDAD: 40;

  PRODUCTO suero_fisiologico {
    PRECIO: 55.00;
    MINIMO: 10;
    MAXIMO: 60;
    CRITICIDAD: ALTA;
  }
}

SIMULAR {
  TRANSACCIONES: [ CONTAR(suero_fisiologico) ];
  REPORTE("reporte_urgencias");
  ESTADO;
}
