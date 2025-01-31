let commentStart = 1;
let path = window.location.pathname.split("/");
let article_id = path[path.length - 1];

async function getComments(start) {
  let response = await fetch(`/api/comments/${article_id}?start=${start}`);
  return (
    await response.json().catch(() => {
      let commentContainer = document.getElementById("comment-container");
      commentContainer.innerHTML = "";
    })
  ).comments;
}

function fillComments(comments) {
  let commentContainer = document.getElementById("comment-container");
  commentContainer.innerHTML = "";
  for (let comment of comments) {
    commentContainer.appendChild(createCommentCard(comment));
  }
}

async function sendComment() {
  let nameBox = document.getElementById("comment-name");
  let bodyBox = document.getElementById("comment-body");
  let commentName = nameBox.value;
  let commentBody = bodyBox.value;
  nameBox.value = "";
  bodyBox.value = "";
  return await fetch(`/api/comments/${article_id}`, {
    method: "POST",
    body: JSON.stringify({ author: commentName, message: commentBody }),
    headers: {
      "Content-Type": "application/json",
    },
  });
}

function makeElement(type, options, children = null) {
  let element = Object.assign(document.createElement(type), options);
  if (children) {
    for (let child of children) {
      element.appendChild(child);
    }
  }
  return element;
}

function createCommentCard(data) {
  let color = "light";

  if (data.official) {
    color = "primary";
  }

  let removeButton = document.createElement("div");

  if (auth == 2) {
    removeButton = makeElement("button", {
      className: "btn btn-danger",
      textContent: "Delete",
    });
    removeButton.addEventListener("click", () =>
      fetch(`/api/comments/${article_id}`, {
        method: "DELETE",
        body: JSON.stringify({ id: data.id }),
        headers: {
          "Content-Type": "application/json",
        },
      }).then(() => loadComments()),
    );
  }
  return makeElement(
    "div",
    {
      className: `card border-${color} mb-3 w-75`,
    },
    [
      makeElement("div", {
        className: `card-header text-${color}`,
        textContent: data.author,
      }),

      makeElement(
        "div",
        {
          className: `card-body text-${color}`,
        },
        [
          makeElement("p", {
            textContent: data.message,
          }),
        ],
      ),

      makeElement("div", {
        className: `card-footer border-${color} text-${color}`,
        textContent: new Date(Math.round(data.time / 1000000)).toLocaleString(),
      }),
      removeButton,
    ],
  );
}

function loadComments() {
  getComments(commentStart).then((comments) => {
    fillComments(comments);
  });
}

function setIndicator() {
  let pageIndicator = document.getElementById("comment-range");
  pageIndicator.textContent = `${commentStart}-${commentStart + 10}`;
}

async function updateCommentCount() {
  response = await fetch(`/api/comments/${article_id}`);
  return (await response.json()).size;
}

function navigateComments(delta) {
  updateCommentCount().then((numComments) => {
    commentStart = Math.min(
      Math.max(commentStart + delta, 1),
      Math.ceil(numComments / 10 - 1) * 10 + 1,
    );
    setIndicator();
    loadComments();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  let commentButton = document.getElementById("comment-submit");
  commentButton.addEventListener("click", () => {
    sendComment().then(loadComments);
  });

  let nextButton = document.getElementById("next-comments");
  let backButton = document.getElementById("previous-comments");
  backButton.addEventListener("click", () => {
    navigateComments(-10);
  });
  nextButton.addEventListener("click", () => {
    navigateComments(10);
  });

  loadComments();
  setIndicator();
});
