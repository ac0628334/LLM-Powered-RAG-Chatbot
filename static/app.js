const API = "http://127.0.0.1:8000";

/* ELEMENTS */

const authScreen =
document.getElementById("authScreen");

const app =
document.getElementById("app");

const chatContainer =
document.getElementById("chatContainer");

const messageInput =
document.getElementById("messageInput");

const fileInput =
document.getElementById("fileInput");

const fileList =
document.getElementById("fileList");

/* TOKEN */

let token =
localStorage.getItem("token");

/* AUTO LOGIN */

if(token){
  showApp();
}

/* SWITCH TABS */

function switchTab(tab){

  document.querySelectorAll(".tab")
  .forEach(t => t.classList.remove("active"));

  if(tab === "login"){

    document.querySelectorAll(".tab")[0]
    .classList.add("active");

    document.getElementById("loginForm")
    .style.display = "block";

    document.getElementById("registerForm")
    .style.display = "none";

  }else{

    document.querySelectorAll(".tab")[1]
    .classList.add("active");

    document.getElementById("loginForm")
    .style.display = "none";

    document.getElementById("registerForm")
    .style.display = "block";
  }
}

/* REGISTER */

async function registerUser(){

  const username =
  document.getElementById("regUsername").value;

  const email =
  document.getElementById("regEmail").value;

  const password =
  document.getElementById("regPassword").value;

  try{

    const response =
    await fetch(`${API}/register`,{

      method:"POST",

      headers:{
        "Content-Type":"application/json"
      },

      body:JSON.stringify({
        username,
        email,
        password
      })
    });

    const data =
    await response.json();

    if(response.ok){

      alert(
        "Registration successful!"
      );

      switchTab("login");

    }else{

      alert(
        data.detail ||
        "Registration failed"
      );
    }

  }catch(error){

    alert(
      "Backend connection failed."
    );
  }
}

/* LOGIN */

async function login(){

  const username =
  document.getElementById("loginUsername").value;

  const password =
  document.getElementById("loginPassword").value;

  const formData =
  new FormData();

  formData.append(
    "username",
    username
  );

  formData.append(
    "password",
    password
  );

  try{

    const response =
    await fetch(`${API}/login`,{

      method:"POST",

      body:formData
    });

    const data =
    await response.json();

    if(data.access_token){

      localStorage.setItem(
        "token",
        data.access_token
      );

      token =
      data.access_token;

      showApp();

    }else{

      alert(
        "Invalid credentials"
      );
    }

  }catch(error){

    alert(
      "Unable to connect to backend."
    );
  }
}

/* SHOW APP */

function showApp(){

  authScreen.classList.add("hidden");

  app.classList.remove("hidden");

  loadHistory();
}

/* LOGOUT */

function logout(){

  localStorage.removeItem("token");

  location.reload();
}

/* SEND MESSAGE */

async function sendMessage(){

  const text =
  messageInput.value.trim();

  if(!text) return;

  // CHECK LOGIN
  const token =
  localStorage.getItem("token");

  if(!token){

    addMessage(
      "Please login first.",
      "bot"
    );

    return;
  }

  // USER MESSAGE
  addMessage(text,"user");

  // CLEAR INPUT
  messageInput.value = "";

  // SHOW TYPING
  showTyping();

  try{

    const response =
    await fetch(`${API}/chat`,{

      method:"POST",

      headers:{
        "Content-Type":"application/json",
        "Authorization":
        `Bearer ${token}`
      },

      body:JSON.stringify({
        question:text,
        history:[]
      })
    });

    // UNAUTHORIZED
    if(response.status === 401){

      removeTyping();

      addMessage(
        "Session expired. Please login again.",
        "bot"
      );

      localStorage.removeItem("token");

      return;
    }

    // OTHER ERRORS
    if(!response.ok){

      removeTyping();

      addMessage(
        "Backend request failed.",
        "bot"
      );

      return;
    }

    const data =
    await response.json();

    removeTyping();

    // ONLY ANSWER
    const answer =
    data.answer ||
    "No response generated.";

    addMessage(answer,"bot");

  }catch(error){

    removeTyping();

    addMessage(
      "Unable to connect to AI server.",
      "bot"
    );

    console.error(error);
  }
}

/* ADD MESSAGE */

function addMessage(text,sender){

  const message =
  document.createElement("div");

  message.classList.add("message");
  message.classList.add(sender);

  message.innerHTML = `
    <div class="message-box">
      ${text}
    </div>
  `;

  chatContainer.appendChild(message);

  chatContainer.scrollTop =
  chatContainer.scrollHeight;
}

/* SHOW TYPING */

function showTyping(){

  const typing =
  document.createElement("div");

  typing.id = "typing";

  typing.classList.add("message");
  typing.classList.add("bot");

  typing.innerHTML = `
    <div class="message-box">
      <span class="spinner"></span>
      Thinking...
    </div>
  `;

  chatContainer.appendChild(typing);

  chatContainer.scrollTop =
  chatContainer.scrollHeight;
}

/* REMOVE TYPING */

function removeTyping(){

  const typing =
  document.getElementById("typing");

  if(typing){
    typing.remove();
  }
}

/* ENTER KEY */

messageInput.addEventListener(
  "keypress",
  function(e){

    if(
      e.key === "Enter" &&
      !e.shiftKey
    ){

      e.preventDefault();

      sendMessage();
    }
  }
);

/* FILE UPLOAD */

fileInput.addEventListener(
  "change",
  async()=>{

    const files =
    fileInput.files;

    if(files.length === 0){
      return;
    }

    const token =
    localStorage.getItem("token");

    if(!token){

      alert(
        "Please login first."
      );

      return;
    }

    const formData =
    new FormData();

    fileList.innerHTML = "";

    for(let file of files){

      formData.append(
        "files",
        file
      );

      const item =
      document.createElement("div");

      item.classList.add("file-item");

      item.innerText =
      `📄 ${file.name}`;

      fileList.appendChild(item);
    }

    try{

      const response =
      await fetch(
        `${API}/ingest/files`,
        {

          method:"POST",

          headers:{
            "Authorization":
            `Bearer ${token}`
          },

          body:formData
        }
      );

      if(response.ok){

        alert(
          "Documents ingested successfully!"
        );

      }else{

        alert(
          "Document ingestion failed."
        );
      }

    }catch(error){

      alert(
        "Backend connection failed."
      );
    }
  }
);

/* INGEST URLS */

async function ingestUrls(){

  const token =
  localStorage.getItem("token");

  if(!token){

    alert(
      "Please login first."
    );

    return;
  }

  const urls =
  document.getElementById("urlInput")
  .value
  .split("\n")
  .filter(Boolean);

  if(urls.length === 0){

    alert(
      "Enter at least one URL."
    );

    return;
  }

  try{

    const response =
    await fetch(
      `${API}/ingest/urls`,
      {

        method:"POST",

        headers:{
          "Content-Type":
          "application/json",

          "Authorization":
          `Bearer ${token}`
        },

        body:JSON.stringify({
          urls
        })
      }
    );

    if(response.ok){

      alert(
        "URLs ingested successfully!"
      );

    }else{

      alert(
        "URL ingestion failed."
      );
    }

  }catch(error){

    alert(
      "Backend connection failed."
    );
  }
}

/* LOAD HISTORY */

async function loadHistory(){

  const token =
  localStorage.getItem("token");

  if(!token) return;

  try{

    const response =
    await fetch(`${API}/history`,{

      headers:{
        "Authorization":
        `Bearer ${token}`
      }
    });

    if(!response.ok){
      return;
    }

    const history =
    await response.json();

    history.forEach(chat=>{

      addMessage(
        chat.question,
        "user"
      );

      addMessage(
        chat.answer,
        "bot"
      );
    });

  }catch(error){

    console.error(
      "Failed to load history"
    );
  }
}