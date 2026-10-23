// Server-side plan resolution for public orders. The ONLY source of a sellable
// plan is the governed public catalog (catalog.json, the same projection that
// renders the storefront). A product that is request_price — every product
// while the EXEC-010 commercial HOLD is active — resolves to null, and the order
// API answers 409. Pricing notes in ops/ are never read here.
import catalog from "../../../catalog.json";

export type GovernedPlan = {
  product_id: string;
  plan_id: string;
  product_name: string;
  plan_name: string;
  price_bdt: number;
  access_type?: string;
  support_terms?: string;
};

type CatalogPlan = {
  plan_id?: string;
  label?: string;
  type?: string;
  access_type?: string;
  bdt?: number;
};

type CatalogProduct = {
  id?: string;
  name?: string;
  request_price?: boolean;
  plans?: CatalogPlan[];
};

const PRODUCTS = new Map<string, CatalogProduct>(
  ((catalog as { products?: CatalogProduct[] }).products || [])
    .filter(p => typeof p.id === "string")
    .map(p => [p.id as string, p]),
);

const SUPPORT_TERMS = "Access method, timing and support terms are confirmed in writing before payment.";

function governed(product: CatalogProduct, plan: CatalogPlan): GovernedPlan | null {
  const accessType = plan.access_type || plan.type;
  if (!plan.plan_id || !plan.label || !accessType || /^shared/i.test(accessType)) return null;
  const price = Number(plan.bdt);
  if (!Number.isInteger(price) || price <= 0) return null;
  return {
    product_id: product.id as string,
    plan_id: plan.plan_id,
    product_name: product.name || (product.id as string),
    plan_name: plan.label,
    price_bdt: price,
    access_type: accessType,
    support_terms: SUPPORT_TERMS,
  };
}

export function resolveGovernedPlan(productId: string, planId: string): GovernedPlan | null {
  const product = PRODUCTS.get(productId);
  if (!product || product.request_price !== false || !Array.isArray(product.plans)) return null;
  const plan = product.plans.find(p => p.plan_id === planId);
  return plan ? governed(product, plan) : null;
}

export function listGovernedPlans() {
  const rows: GovernedPlan[] = [];
  for (const product of PRODUCTS.values()) {
    if (product.request_price !== false || !Array.isArray(product.plans)) continue;
    for (const plan of product.plans) {
      const row = governed(product, plan);
      if (row) rows.push(row);
    }
  }
  return rows;
}
