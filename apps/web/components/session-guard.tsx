/**
 * Back/forward protection for private pages.
 *
 * Browsers may show a stored copy of a page on Back/Forward without asking the server
 * (the back/forward cache, or the HTTP cache when a page isn't `no-store`; Next's dev
 * server sends `no-cache` on purpose). After signing out, that copy could still show
 * private data. This inline script runs before the page paints: on a back/forward load it
 * hides the page, re-checks the session, and replaces the page with sign-in on 401.
 *
 * It is static text with no user data. When the CSP arrives (Milestone 5) it gets a nonce.
 */
const SCRIPT = `(function(){
  function check(){
    var s=document.createElement('style');
    s.textContent='body{visibility:hidden}';
    document.head.appendChild(s);
    fetch('/api/v1/auth/me',{credentials:'same-origin',cache:'no-store'}).then(function(r){
      if(r.status===401){location.replace('/sign-in?returnTo='+encodeURIComponent(location.pathname+location.search));}
      else{s.remove();}
    }).catch(function(){s.remove();});
  }
  var nav=performance.getEntriesByType&&performance.getEntriesByType('navigation')[0];
  if(nav&&nav.type==='back_forward'){check();}
  addEventListener('pageshow',function(e){if(e.persisted){check();}});
})();`;

export function SessionGuard() {
  // Static script text, no user input.
  return <script dangerouslySetInnerHTML={{ __html: SCRIPT }} />;
}
