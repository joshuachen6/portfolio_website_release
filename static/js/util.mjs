export function parseHtml(input) {
    let template = document.createElement('template');
    template.innerHTML = input;
    return template.content.firstChild;
}