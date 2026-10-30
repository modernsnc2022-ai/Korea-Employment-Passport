import { collect } from "../src/index.mjs";
console.log("NODE_NETWORK_CONTEXT", JSON.stringify({
  proxyPresent: Boolean(process.env.HTTPS_PROXY || process.env.https_proxy),
  envProxyEnabled: process.env.NODE_USE_ENV_PROXY === "1",
  nodeVersion: process.version
}));
try {
  const d = await collect();
  const kp = d.records.filter(x=>x.provider==="kp2mi").length;
  const hr = d.records.filter(x=>x.provider==="hrdk").length;
  console.log("KEP_OFFICIAL_REAL_HTTP_PASS", kp, hr);
} catch (err) {
  console.log("KEP_OFFICIAL_REAL_HTTP_FAIL_CLOSED",JSON.stringify({
    type:err?.name, message:err?.message, causeCode:err?.cause?.code,
    causeType:err?.cause?.name
  }));
  process.exitCode=2;
}
