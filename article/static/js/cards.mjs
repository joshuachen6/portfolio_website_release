import {parseHtml} from "../../../static/js/util.mjs";

let CARD_SIZE = 12;

function createCard(image, title, link){
    let container = document.createElement('div');
    container.classList.add('col', 'd-flex', 'justify-content-center');
    let element = parseHtml(
        `<div class="card border-white bg-dark clickable" style="width: ${CARD_SIZE}rem;">
            <div class="border-bottom border-white" style="aspect-ratio: 1;">
                <img class="card-img-top bg-secondary" src="${image}" style="max-width: 100%; max-height: 100%; object-fit: contain">
            </div>
            <div class="card-body" style="aspect-ratio: 4">
                <p class="card-text">${title}</p>
            </div>
        </div>`
    );
    container.appendChild(element);
    element.addEventListener('click', ()=>{
        window.location.href = link;
    });
    return container;
}

class CardDeck {
    constructor(element) {
        this.row = element;
        let cardDeck = element.getElementsByClassName('card-deck')[0];
        let fontSize = window.getComputedStyle(cardDeck).fontSize;
        this.size = Math.floor(cardDeck.offsetWidth / (Number(fontSize.substring(0, fontSize.length-2)) * CARD_SIZE + 24));
        this.height = Number(fontSize.substring(0, fontSize.length-2)) * CARD_SIZE * 1.25;
        this.category = cardDeck.id;
        this.start = 1;
        this.max = 0;

        fetch(`/api/browse?tag=${this.category}`).then((response)=>{
            response.json().then((json)=>{
                this.max = json.articles;
            });
        });
        
        this.cardContainer = document.createElement('div');
        this.cardContainer.style.height = `${this.height}px`;

        cardDeck.classList.add('bg-dark', 'bg-gradient', 'rounded');
        this.cardContainer.classList.add('row');

        let left = element.getElementsByClassName('left button')[0];
        left.addEventListener('click', () => this.scrollCards(Math.max(1, this.start-this.size)));
        let right = element.getElementsByClassName('right button')[0];
        right.addEventListener('click', () => {
            if (this.start + this.size <= this.max)
            this.scrollCards(this.start + this.size);
        });

        this.fillCards();
        cardDeck.appendChild(this.cardContainer);
        if (this.category === window.location.hash.substring(1)) {
            cardDeck.scrollIntoView({block: "center"});
        }
    }

    scrollCards(start) {
        if (start !== this.start) {
            this.start = start;
            this.fillCards();
        }
    }

    fillCards() {
        fetch(`/api/browse?tag=${this.category}&start=${this.start}&size=${this.size}`).then((response)=>{
            response.json().then((json)=>{
                this.cardContainer.innerHTML = '';
                let promises = [];
                for (let index = 0; index < this.size; index++) {
                    let placeholder = document.createElement('div');
                    placeholder.style.width = `${CARD_SIZE}em`;
                    this.cardContainer.appendChild(placeholder);
                    if (index < json.articles.length) {
                        let id = json.articles[index];
                        promises.push(fetch(`/api/article/${id}`).then((response)=>{
                            return response.json().then((json)=>{
                                let card = createCard(json.icon, json.title, `/article/${id}`);
                                card.classList.add('fade');
                                placeholder.replaceWith(card);
                            });
                        }))
                    }
                }
                Promise.all(promises).then(()=>{
                    for (let i = 0; i < this.cardContainer.children.length; i++) {
                        let child = this.cardContainer.children[i];
                        setTimeout(()=>{
                            child.classList.add('show');
                        }, i*250);
                    }
                    this.row.classList.replace('hidden', 'show');
                })
            });
        });
    }
}

document.addEventListener('DOMContentLoaded', ()=>{
   let deckContainer = document.getElementById("decks");
   let response = fetch("/api/tags").then((response)=>{
    response.json().then(
      (json)=>{
        let tags = json.tags;
        for (let tag of tags) {

          let element = parseHtml(`<div class="deck-container row hidden fade">
          <h3>${tag.name}</h3>
          <div class="col-auto d-flex justify-content-center align-items-center">
              <button class="left button">
                  <span class="material-icons icon-m">west</span>
              </button>
          </div>
          <div class="card-deck col d-flex justify-content-center" id="${tag.id}">

          </div>
          <div class="col-auto d-flex justify-content-center align-items-center">
              <button class="right button">
                  <span class="material-icons icon-m">east</span>
              </button>
          </div>
          <hr class="border-2 mt-5 mb-5 rounded">
      </div>`);
        
          deckContainer.appendChild(element);
          new CardDeck(element);
        }
      }
    );
  }); 
});

window.addEventListener('resize', ()=>window.location.reload());
