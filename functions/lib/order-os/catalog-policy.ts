import pricing from "../../../ops/PRICING-V2-2026-09-17.json";

export type GovernedPlan = {
  product_id: string;
  plan_id: string;
  product_name: string;
  plan_name: string;
  price_bdt: number;
  access_type?: string;
  support_terms?: string;
};

type PolicyPlan = {
  plan_id?: string;
  label?: string;
  access_type?: string;
  bdt?: number;
};

type ProductPolicy = {
  mode?: string;
  plans?: PolicyPlan[];
};

const PRODUCTS = pricing.approved_products as Record<string, ProductPolicy>;

function titleFromProductId(productId: string) {
  return productId
    .split("-")
    .map(part => part ? part[0].toUpperCase() + part.slice(1) : part)
    .join(" ")
    .replace("Chatgpt", "ChatGPT")
    .replace("Github", "GitHub")
    .replace("Ai", "AI");
}

export function resolveGovernedPlan(productId: string, planId: string): GovernedPlan | null {
  const product = PRODUCTS[productId];
  if (!product || product.mode === "inquiry" || !Array.isArray(product.plans)) return null;

  const plan = product.plans.find(p => p.plan_id === planId);
  if (!plan || !plan.plan_id || !plan.label || !plan.access_type || !Number.isFinite(plan.bdt)) return null;

  const positioning = (pricing.positioning as Record<string, string>)[plan.access_type];
  return {
    product_id: productId,
    plan_id: plan.plan_id,
    product_name: titleFromProductId(productId),
    plan_name: plan.label,
    price_bdt: Number(plan.bdt),
    access_type: plan.access_type,
    support_terms: positioning || "Confirm access and support terms before payment.",
  };
}

export function listGovernedPlans() {
  const rows: GovernedPlan[] = [];
  for (const [productId, product] of Object.entries(PRODUCTS)) {
    if (product.mode === "inquiry" || !Array.isArray(product.plans)) continue;
    for (const plan of product.plans) {
      if (!plan.plan_id || !plan.label || !plan.access_type || !Number.isFinite(plan.bdt)) continue;
      rows.push({
        product_id: productId,
        plan_id: plan.plan_id,
        product_name: titleFromProductId(productId),
        plan_name: plan.label,
        price_bdt: Number(plan.bdt),
        access_type: plan.access_type,
        support_terms: (pricing.positioning as Record<string, string>)[plan.access_type] || "Confirm access and support terms before payment.",
      });
    }
  }
  return rows;
}
