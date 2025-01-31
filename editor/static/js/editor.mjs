import {parseHtml} from "../../../static/js/util.mjs";

let urlParams = new URLSearchParams(window.location.search);
let saveInterval = 10 * 1000;
let edited = false;

// declare elements
let metaForm = document.getElementById('meta-form');

// custom image embed
class ImageEmbed extends Quill.import('formats/image') {
    static create(value) {
        if (typeof value == 'string') {
            value = JSON.parse(value);
        }
        let url = value.imageSrc;
        if (url instanceof Blob) {
            url = URL.createObjectURL(value.imageSrc);
        }
        let blot = super.create(url);
        blot.src = url;
        blot.setAttribute('data-image', value.image);
        if ('style' in value) {
            blot.setAttribute('style', value.style);
        }
        return blot;
    }
}

ImageEmbed.blotName = 'image-embed';
ImageEmbed.tagName = 'IMG';
Quill.register(ImageEmbed);

// custom video thumbnail
class VideoThumbnail extends ImageEmbed {
    static create(value) {
        let blot = super.create(value);
        if (typeof value == 'string') {
            value = JSON.parse(value);
            if (value.hasOwnProperty('video')) {
                blot.setAttribute('data-video', value.video);
            }
        } else {
            blot.setAttribute('data-video', value.video);
        }
        return blot;
    }
}

VideoThumbnail.blotName = 'thumbnail';
VideoThumbnail.tagName = 'IMG';
Quill.register(VideoThumbnail);

let fileUploads = [];

const quill = new Quill('#editor', {
    modules: {
        imageResize: {},
        toolbar: [
            ['bold', 'italic', 'underline', 'strike'],
            ['blockquote', 'code-block', 'link'],

            [{'list': 'ordered'}, {'list': 'bullet'}],
            [{'script': 'sub'}, {'script': 'super'}],
            [{'indent': '-1'}, {'indent': '+1'}],

            [{'size': []}],
            [{'header': []}],

            [{'color': []}, {'background': []}],
            [{'font': []}],
            [{'align': []}],
            ['image', 'video'],

            ['clean']
        ],
    },
    placeholder: 'Compose an epic...',
    theme: 'snow'  // or 'bubble'
});

quill.on('text-change', flagEdit);

async function openFile(filetype = '*') {
    return new Promise((resolve, reject) => {
        let filedialog = Object.assign(document.createElement('input'), {type: 'file', accept: filetype});
        filedialog.addEventListener('change', () => {
            resolve(filedialog.files[0]);
        });
        filedialog.click();
    });
}

function addImage() {
    openFile('image/*').then((imageFile) => {
        fileUploads.push(imageFile);
        let cursor = quill.getSelection().index;
        quill.insertEmbed(cursor, 'image-embed', {imageSrc: imageFile, image: imageFile.name});
    });
}

function addVideo() {
    openFile('video/*').then((videoFile) => {
        fileUploads.push(videoFile);
        let video = document.createElement('video');
        video.addEventListener('canplay', () => {
            video.play();
            let canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            let context = canvas.getContext('2d');
            context.drawImage(video, 0, 0);
            let playIcon = document.createElement('img');
            playIcon.addEventListener('load', () => {
                context.drawImage(playIcon, canvas.width / 2 - playIcon.width / 2, canvas.height / 2 - playIcon.height / 2);
                canvas.toBlob((thumbnailBlob) => {
                    fetch('/api/uuid').then(
                        (response) => {
                            response.json().then((json) => {
                                let uuid = json['uuid'];
                                let thumbnailFile = new File([thumbnailBlob], `${uuid}.${thumbnailBlob.type.split('/')[1]}`)
                                fileUploads.push(thumbnailFile);
                                let cursor = quill.getSelection().index;
                                quill.insertEmbed(cursor, 'thumbnail', {
                                    imageSrc: thumbnailFile,
                                    image: thumbnailFile.name,
                                    video: videoFile.name
                                });
                            })
                        }
                    )
                });
                video.pause();
            });
            playIcon.src = '/static/images/video_icon.png';
        })
        video.src = URL.createObjectURL(videoFile);
    });
}

let toolbar = quill.getModule('toolbar');
toolbar.addHandler('video', addVideo);
toolbar.addHandler('image', addImage);

async function sendData() {
    let zipper = new JSZip();
    let formData = new FormData();
    let editorContent = document.getElementsByClassName('ql-editor')[0];
    let currentFiles = [];

    let editorWidth = parseFloat(editorContent.offsetWidth);
    for (let element of editorContent.getElementsByTagName('img')) {
        if (element.hasAttribute('data-image')) {
            currentFiles.push(element.getAttribute('data-image'));
        }
        if (element.hasAttribute('data-video')) {
            currentFiles.push(element.getAttribute('data-video'));
        }
        element.setAttribute('data-width', `${(element.width/editorWidth) * 100}%`);

    }
    for (let file of fileUploads) {
        let name = file.name;
        if (currentFiles.includes(name)) {
            zipper.file(name, file);
        }
    }

    let data = {
        content: editorContent.innerHTML,
        title: document.getElementById('title-input').value,
        date: document.getElementById('date-input').value,
        tags: document.getElementById('tag-input').value,
        visibility: document.getElementById('visibility-input').checked,
    };

    let iconUpload = document.getElementById('icon-input').files;

    if (iconUpload.length > 0) {
        let icon = iconUpload[0];
        data['icon'] = icon.name;
        zipper.file(icon.name, icon);
    }
    formData.append('json', JSON.stringify(data));
    return zipper.generateAsync({type: 'blob'}).then(
        (blob) => {
            formData.append('zip', blob);
            return fetch(
                `/editor?article_id=${urlParams.get('article_id')}`,
                {
                    method: 'PUT',
                    body: formData
                }
            ).then((response) => {
                saveAlert();
                // Update the content
                for (let image of editorContent.getElementsByTagName('img')) {
                    image.src = `/static/uploads/${urlParams.get('article_id')}/${image.getAttribute('data-image')}`
                }
                fileUploads = [];
                if (data.hasOwnProperty('icon')) {
                    iconSelector.value = '';
                    let iconView = document.getElementById('icon-display');
                    iconView.src = `/static/uploads/${urlParams.get('article_id')}/${data['icon']}`;
                }
            }).catch(
                (error) => {
                    window.alert('Failed to save: ' + JSON.stringify(error, Object.getOwnPropertyNames(error)));
                }
            )
        }
    );
}

function saveAlert() {
    let alertBox = document.getElementById('alert-box');
    let alert = parseHtml(`<div class="alert alert-success" role="alert">Saved ${new Date(Date.now()).toLocaleTimeString()}</div>`);
    alertBox.children[0].replaceWith(alert);
}

function warnUnsaved() {
    let alertBox = document.getElementById('alert-box');
    alertBox.children[0].classList.replace('alert-success', 'alert-warning')
}


//This is the code for uploading the contents
let saveButton = document.getElementById('save-button');
saveButton.addEventListener('click', () => {
    sendData().then(
        ()=>{
            if (window.confirm('Exit?')) {
                window.location.href = `/article/${urlParams.get('article_id')}`;
            }
        }
    );
});
let iconSelector = document.getElementById('icon-input');
iconSelector.value = null;
let deleteButton = document.getElementById('delete-button');
deleteButton.addEventListener('click', () => {
    if (window.confirm('Delete permanently?')) {
        fetch(`/editor?article_id=${urlParams.get('article_id')}`, {
            method: 'DELETE'
        }).then(() => {
            window.location.href = '/';
        });
    }
});
iconSelector.addEventListener('change', () => {
    let display = document.getElementById('icon-display');
    display.src = URL.createObjectURL(iconSelector.files[0]);
});

function checkForSend() {
    if (edited) {
        edited = false;
        sendData();
    }
}

function flagEdit() {
    edited = true;
    warnUnsaved();
}

setInterval(checkForSend, saveInterval);

metaForm.addEventListener('change', flagEdit);
metaForm.addEventListener('submit', (e)=>e.preventDefault());
