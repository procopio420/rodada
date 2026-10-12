// Exact presentation mapping from the photographed pilot menu; no product mutations.
const menuGroups: Record<string, { source: string; label: string }> = {
  "Arroz Negro com Frutos do Mar": {
    "source": "Pratos",
    "label": "Pratos quentes"
  },
  "Costelinha de Porco com Batata": {
    "source": "Pratos",
    "label": "Pratos quentes"
  },
  "Jil\u00f3 Recheado": {
    "source": "Pratos",
    "label": "Pratos quentes"
  },
  "Paleta Su\u00edna Defumada - Inteira": {
    "source": "Pratos",
    "label": "Pratos quentes"
  },
  "Paleta Su\u00edna Defumada - Meia": {
    "source": "Pratos",
    "label": "Pratos quentes"
  },
  "T\u00e1bua de Frios": {
    "source": "Pratos",
    "label": "Petiscos e por\u00e7\u00f5es"
  },
  "Por\u00e7\u00e3o de Batata Frita - Tradicional": {
    "source": "Por\u00e7\u00f5es",
    "label": "Petiscos e por\u00e7\u00f5es"
  },
  "Por\u00e7\u00e3o de Batata Frita - com Calabresa": {
    "source": "Por\u00e7\u00f5es",
    "label": "Petiscos e por\u00e7\u00f5es"
  },
  "Por\u00e7\u00e3o de Coxinha da Asa": {
    "source": "Por\u00e7\u00f5es",
    "label": "Petiscos e por\u00e7\u00f5es"
  },
  "Por\u00e7\u00e3o de Isca de Frango": {
    "source": "Por\u00e7\u00f5es",
    "label": "Petiscos e por\u00e7\u00f5es"
  },
  "\u00c1gua Mamba sem G\u00e1s": {
    "source": "Bebidas",
    "label": "\u00c1guas"
  },
  "\u00c1gua Mamba com G\u00e1s": {
    "source": "Bebidas",
    "label": "\u00c1guas"
  },
  "\u00c1gua com G\u00e1s": {
    "source": "Bebidas",
    "label": "\u00c1guas"
  },
  "\u00c1gua sem G\u00e1s": {
    "source": "Bebidas",
    "label": "\u00c1guas"
  },
  "Ativ Plus": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "Fys Sabores": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Coca-Cola 200 ml": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Coca-Cola Lata": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Coca-Cola Zero Lata": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Energ\u00e9tico Monster": {
    "source": "Bebidas",
    "label": "Energ\u00e9ticos e isot\u00f4nicos"
  },
  "Red Bull 250 ml": {
    "source": "Bebidas",
    "label": "Energ\u00e9ticos e isot\u00f4nicos"
  },
  "Red Bull 355 ml": {
    "source": "Bebidas",
    "label": "Energ\u00e9ticos e isot\u00f4nicos"
  },
  "TNT": {
    "source": "Bebidas",
    "label": "Energ\u00e9ticos e isot\u00f4nicos"
  },
  "Fanta Uva": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Fanta Laranja 200 ml": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Fanta Laranja Lata": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Gatorade": {
    "source": "Bebidas",
    "label": "Energ\u00e9ticos e isot\u00f4nicos"
  },
  "Guaran\u00e1": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Guaraviton": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "H2O": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "H2O Limonetto": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Ice Tea": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "Kapo": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "Schweppes": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Sprite": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  },
  "Suco DV Goiaba Lata": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "Suco DV Laranja 200 ml": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "Suco Laranja Lata": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "Suco DV P\u00eassego Lata": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "Suco DV Uva 200 ml": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "Suco DV Uva Lata": {
    "source": "Bebidas",
    "label": "Sucos e outras bebidas"
  },
  "T\u00f4nica Lata": {
    "source": "Bebidas",
    "label": "Refrigerantes"
  }
};
export const normalizeCatalogSearch = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").trim();
export function attendanceCategory(product: { name: string; category?: string }) {
  const mapped = menuGroups[product.name];
  return mapped && product.category === mapped.source ? mapped.label : product.category?.trim() || "Outros";
}
export const attendanceCategoryOrder = ["Cervejas", "Refrigerantes", "Águas", "Sucos e outras bebidas", "Energéticos e isotônicos", "Drinks", "Destilados", "Petiscos e porções", "Salgados", "Pratos quentes", "Caldos", "Outros"];
