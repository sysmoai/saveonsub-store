export type GovernedPlan = {
  product_id: string;
  plan_id: string;
  product_name: string;
  plan_name: string;
  price_bdt: number;
  access_type?: string;
  support_terms?: string;
};

// TEMPORARY SCAFFOLD ONLY.
// Production must replace this object during the build from the governed
// pricing policy/catalog. It intentionally contains only a small safe subset
// so this branch cannot silently become a second pricing source of truth.
const PLANS: Record<string, GovernedPlan> = {
  "chatgpt-plus:personal": {
    product_id: "chatgpt-plus",
    plan_id: "personal",
    product_name: "ChatGPT Plus",
    plan_name: "Customer-specific access",
    price_bdt: 3390,
    access_type: "customer-specific",
    support_terms: "Confirm order-specific support terms before payment",
  },
  "chatgpt-go:personal": {
    product_id: "chatgpt-go",
    plan_id: "personal",
    product_name: "ChatGPT Go",
    plan_name: "Customer-specific access",
    price_bdt: 1299,
    access_type: "customer-specific",
    support_terms: "Confirm order-specific support terms before payment",
  },
};

export function resolveGovernedPlan(productId: string, planId: string): GovernedPlan | null {
  return PLANS[`${productId}:${planId}`] ?? null;
}
