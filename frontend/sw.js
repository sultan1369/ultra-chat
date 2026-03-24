self.addEventListener("install", e=>{
  self.skipWaiting();
});

self.addEventListener("fetch", e=>{
  // minimal caching
});