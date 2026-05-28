/**
 * Dynamic Pages Deployment Configuration
 * 
 * Detecta automaticamente o Pages deployment URL baseado em headers
 * e environment variables, sem precisar de atualizações manuais.
 */

/**
 * Get the current Pages deployment URL dynamically
 * Priority:
 * 1. Environment variable (set by build process)
 * 2. Window origin (for client-side code)
 * 3. Fallback to known deployments
 */
export function getPagesDeploymentUrl() {
  // Check if we're in server context (Next.js build/API routes)
  if (typeof window === "undefined") {
    // Server-side: use environment variable
    const envUrl = process.env.NEXT_PUBLIC_PAGES_DEPLOYMENT_URL || 
                   process.env.PAGES_DEPLOYMENT_URL;
    if (envUrl) {
      return envUrl.replace(/\/$/, "");
    }
    // Fallback for server context
    return "https://954f6265.syntexa-frontend.pages.dev";
  }
  
  // Client-side: detect from current location
  if (typeof window !== "undefined" && window.location) {
    const host = window.location.host;
    
    // If we're running on Pages deployment directly
    if (host.includes("pages.dev")) {
      return `https://${host}`.replace(/\/$/, "");
    }
    
    // If running on custom domain, return the Pages deployment from meta tag or env
    const metaTag = document.querySelector('meta[name="pages-deployment-url"]');
    if (metaTag && metaTag.content) {
      return metaTag.content.replace(/\/$/, "");
    }
    
    // Check environment variable set during build
    if (typeof process !== "undefined" && process.env) {
      const envUrl = process.env.NEXT_PUBLIC_PAGES_DEPLOYMENT_URL;
      if (envUrl) {
        return envUrl.replace(/\/$/, "");
      }
    }
  }
  
  // Fallback to known deployment
  return "https://954f6265.syntexa-frontend.pages.dev";
}

/**
 * Get the frontend base URL (public domain)
 * Priority:
 * 1. Environment variable
 * 2. Current window origin (if not Pages deployment)
 * 3. Fallback to production domain
 */
export function getFrontendBaseUrl() {
  // Server-side
  if (typeof window === "undefined") {
    return process.env.FRONTEND_BASE_URL || 
           process.env.NEXT_PUBLIC_FRONTEND_BASE_URL || 
           "https://syntexabr.com.br";
  }
  
  // Client-side
  if (typeof window !== "undefined" && window.location) {
    // Environment variable has priority
    if (typeof process !== "undefined" && process.env) {
      const envUrl = process.env.NEXT_PUBLIC_FRONTEND_BASE_URL;
      if (envUrl && !envUrl.includes("pages.dev")) {
        return envUrl.replace(/\/$/, "");
      }
    }
    
    // If not on Pages deployment, use current origin
    const host = window.location.host;
    if (!host.includes("pages.dev")) {
      return `https://${host}`.replace(/\/$/, "");
    }
  }
  
  // Fallback
  return "https://syntexabr.com.br";
}

/**
 * Initialize meta tag with current deployment URL
 * Useful for JavaScript that needs to know the Pages URL
 */
export function initPagesDeploymentMeta() {
  if (typeof document === "undefined") return;
  
  const existing = document.querySelector('meta[name="pages-deployment-url"]');
  if (existing) return;
  
  const meta = document.createElement("meta");
  meta.name = "pages-deployment-url";
  meta.content = getPagesDeploymentUrl();
  document.head.appendChild(meta);
}
