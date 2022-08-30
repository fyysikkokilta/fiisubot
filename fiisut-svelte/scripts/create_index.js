import lunr from 'lunr';
import lunr_stemmer from 'lunr-languages/lunr.stemmer.support.js';
import lunr_fi from 'lunr-languages/lunr.fi.js';
import lunr_sv from 'lunr-languages/lunr.sv.js';
import lunr_multi from 'lunr-languages/lunr.multi.js';
import fs from 'fs';

const songs = JSON.parse(fs.readFileSync(process.argv[2])).map((e,i) => ({...e, index: i}))

lunr_stemmer(lunr)
lunr_multi(lunr)
lunr_fi(lunr)
lunr_sv(lunr)

const idx = lunr(function () {
  this.use(lunr.multiLanguage('en', 'fi', 'sv'))
  this.use(lunr.fi)
  this.use(lunr.sv)
  this.ref('index')
  this.field('name', { boost: 10 })
  this.field('lyrics')

  songs.forEach(doc => this.add(doc))

})

fs.writeFile(process.argv[3], JSON.stringify(idx), {}, e => {
  if (e!==null)
    console.error("Saving data to file failed", e)
})
