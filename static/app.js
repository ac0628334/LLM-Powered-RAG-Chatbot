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

/* CHAT STORAGE */

let chatSessions =
JSON.parse(
  localStorage.getItem("chatSessions")
) || [];

let currentChatId = null;

/* AUTO LOGIN */

if(token){

  showApp();
}

/* PROFILE LOAD */

const storedUsername =
localStorage.getItem("username");

const storedEmail =
localStorage.getItem("email");

if(storedUsername){

  document
  .getElementById(
    "sidebarUsername"
  )
  .innerText = storedUsername;

  document
  .getElementById(
    "profileAvatar"
  )
  .innerText =
  storedUsername
  .charAt(0)
  .toUpperCase();
}

if(storedEmail){

  document
  .getElementById(
    "sidebarEmail"
  )
  .innerText = storedEmail;
}

/* SWITCH TABS */

function switchTab(tab){

  document
  .querySelectorAll(".tab")
  .forEach(tabBtn=>{

    tabBtn.classList.remove("active");
  });

  if(tab === "login"){

    document
    .querySelectorAll(".tab")[0]
    .classList.add("active");

    document
    .getElementById("loginForm")
    .style.display = "block";

    document
    .getElementById("registerForm")
    .style.display = "none";

  }else{

    document
    .querySelectorAll(".tab")[1]
    .classList.add("active");

    document
    .getElementById("loginForm")
    .style.display = "none";

    document
    .getElementById("registerForm")
    .style.display = "block";
  }
}

/* REGISTER */

async function registerUser(){

  try{

    const username =
    document.getElementById(
      "regUsername"
    ).value;

    const email =
    document.getElementById(
      "regEmail"
    ).value;

    const password =
    document.getElementById(
      "regPassword"
    ).value;

    const passwordRegex =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{4,}$/;

    if(!passwordRegex.test(password)){

      alert(
        "Password must contain uppercase, lowercase, number, special character and minimum 4 characters"
      );

      return;
    }

    const response =
    await fetch(`${API}/register`,{

      method:"POST",

      headers:{
        "Content-Type":
        "application/json"
      },

      body:JSON.stringify({
        username,
        email,
        password
      })
    });

    if(response.ok){

      alert(
        "Registration successful"
      );

      switchTab("login");

    }else{

      const error =
      await response.json();

      alert(
        error.detail ||
        "Registration failed"
      );
    }

  }catch(error){

    console.error(error);

    alert(
      "Backend connection failed"
    );
  }
}

/* LOGIN */

async function login(){

  try{

    const identifier =
    document.getElementById(
      "loginUsername"
    ).value;

    const password =
    document.getElementById(
      "loginPassword"
    ).value;

    if(!identifier || !password){

      alert(
        "Please enter username/email and password"
      );

      return;
    }

    const formData =
    new FormData();

    formData.append(
      "username",
      identifier
    );

    formData.append(
      "password",
      password
    );

    const response =
    await fetch(`${API}/login`,{

      method:"POST",

      body:formData
    });

    const data =
    await response.json();

    const accessToken =
      data.access_token ||
      data.token;

    if(accessToken){

      token = accessToken;

      localStorage.setItem(
        "token",
        accessToken
      );

      localStorage.setItem(
        "username",
        data.username
      );

      localStorage.setItem(
        "email",
        data.email
      );

      document
      .getElementById(
        "sidebarUsername"
      )
      .innerText = data.username;

      document
      .getElementById(
        "sidebarEmail"
      )
      .innerText = data.email;

      document
      .getElementById(
        "profileAvatar"
      )
      .innerText =
      data.username
      .charAt(0)
      .toUpperCase();

      showApp();

    }else{

      alert(
        "Login failed"
      );
    }

  }catch(error){

    console.error(error);

    alert(
      "Unable to connect to backend"
    );
  }
}

/* SHOW APP */

function showApp(){

  authScreen.style.display =
  "none";

  app.style.display =
  "flex";

  renderRecentChats();
}

/* LOGOUT */

function logout(){

  localStorage.removeItem("token");
  localStorage.removeItem("username");
  localStorage.removeItem("email");

  location.reload();
}

/* NEW CHAT */

function startNewChat(){

  currentChatId =
  Date.now();

  const newChat = {

    id:currentChatId,

    title:"New Chat",

    messages:[],

    createdAt:
    new Date()
    .toLocaleString()
  };

  chatSessions.unshift(
    newChat
  );

  localStorage.setItem(
    "chatSessions",
    JSON.stringify(chatSessions)
  );

  renderRecentChats();

  chatContainer.innerHTML = `

    <div class="hero">

      <div class="hero-icon">
        ✦
      </div>

      <h1>
        How can I help you today?
      </h1>

      <p>
        Upload documents and interact with your AI knowledge base.
      </p>

    </div>
  `;
}

/* SAVE CHAT */

function saveMessageToSession(
  question,
  answer
){

  if(!currentChatId){

    startNewChat();
  }

  const chat =
  chatSessions.find(
    c => c.id === currentChatId
  );

  if(!chat) return;

  if(chat.title === "New Chat"){

    chat.title =
    question.substring(0,40);
  }

  chat.messages.push({

    question,
    answer
  });

  localStorage.setItem(
    "chatSessions",
    JSON.stringify(chatSessions)
  );

  renderRecentChats();
}

/* RECENT CHATS */

function renderRecentChats(){

  const container =
  document.getElementById(
    "recentChats"
  );

  container.innerHTML = "";

  chatSessions.forEach(chat=>{

    const item =
    document.createElement("div");

    item.classList.add(
      "chat-folder"
    );

    item.innerHTML = `

      <div class="chat-folder-title">
        ${chat.title}
      </div>

      <div class="chat-folder-time">
        ${chat.createdAt}
      </div>
    `;

    item.onclick = ()=>{

      openChat(chat.id);
    };

    container.appendChild(item);
  });
}

/* OPEN CHAT */

function openChat(chatId){

  currentChatId = chatId;

  const chat =
  chatSessions.find(
    c => c.id === chatId
  );

  if(!chat) return;

  chatContainer.innerHTML = "";

  chat.messages.forEach(msg=>{

    addMessage(
      msg.question,
      "user"
    );

    addMessage(
      msg.answer,
      "bot"
    );
  });
}

/* SEARCH */

document
.getElementById("historySearch")
.addEventListener(
  "input",
  function(){

    const keyword =
    this.value.toLowerCase();

    const filtered =
    chatSessions.filter(chat=>

      chat.title
      .toLowerCase()
      .includes(keyword)

      ||

      chat.messages.some(m=>

        m.question
        .toLowerCase()
        .includes(keyword)

        ||

        m.answer
        .toLowerCase()
        .includes(keyword)
      )
    );

    const container =
    document.getElementById(
      "recentChats"
    );

    container.innerHTML = "";

    filtered.forEach(chat=>{

      const item =
      document.createElement("div");

      item.classList.add(
        "chat-folder"
      );

      item.innerHTML = `

        <div class="chat-folder-title">
          ${chat.title}
        </div>

        <div class="chat-folder-time">
          Keyword matched
        </div>
      `;

      item.onclick = ()=>{

        openChat(chat.id);
      };

      container.appendChild(item);
    });
  }
);

/* SEND MESSAGE */

async function sendMessage(){

  try{

    const text =
    messageInput.value.trim();

    if(!text) return;

    if(!token){

      alert(
        "Please login first"
      );

      return;
    }

    addMessage(
      text,
      "user"
    );

    messageInput.value = "";

    showTyping();

    const response =
    await fetch(`${API}/chat`,{

      method:"POST",

      headers:{
        "Content-Type":
        "application/json",

        "Authorization":
        `Bearer ${token}`
      },

      body:JSON.stringify({

        question:text,
        history:[]
      })
    });

    if(response.status === 401){

      removeTyping();

      alert(
        "Session expired. Login again."
      );

      localStorage.removeItem(
        "token"
      );

      return;
    }

    const data =
    await response.json();

    removeTyping();

    const answer =
      data.answer ||
      "No response generated";

    addMessage(
      answer,
      "bot"
    );

    saveMessageToSession(
      text,
      answer
    );

  }catch(error){

    console.error(error);

    removeTyping();

    addMessage(
      "Backend connection failed",
      "bot"
    );
  }
}

/* ADD MESSAGE */

function addMessage(
  text,
  sender
){

  const message =
  document.createElement("div");

  message.classList.add(
    "message"
  );

  message.classList.add(
    sender
  );

  message.innerHTML = `

    <div class="message-box">
      ${marked.parse(text)}
    </div>
  `;

  chatContainer.appendChild(
    message
  );

  document
  .querySelectorAll("pre code")
  .forEach(block=>{

    hljs.highlightElement(
      block
    );
  });

  chatContainer.scrollTop =
  chatContainer.scrollHeight;
}

/* TYPING */

function showTyping(){

  const typing =
  document.createElement("div");

  typing.id = "typing";

  typing.classList.add(
    "message"
  );

  typing.classList.add(
    "bot"
  );

  typing.innerHTML = `

    <div class="message-box">
      <span class="spinner"></span>
      Thinking...
    </div>
  `;

  chatContainer.appendChild(
    typing
  );

  chatContainer.scrollTop =
  chatContainer.scrollHeight;
}

function removeTyping(){

  const typing =
  document.getElementById(
    "typing"
  );

  if(typing){

    typing.remove();
  }
}

/* ENTER KEY */

messageInput
.addEventListener(
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

    try{

      const files =
      fileInput.files;

      if(files.length === 0){
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

        item.classList.add(
          "file-item"
        );

        item.innerHTML = `
          📄 ${file.name}
        `;

        fileList.appendChild(
          item
        );
      }

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
          "Files uploaded successfully"
        );

      }else{

        alert(
          "File upload failed"
        );
      }

    }catch(error){

      console.error(error);

      alert(
        "Backend connection failed"
      );
    }
  }
);

/* INGEST URLS */

async function ingestUrls(){

  try{

    const urls =
    document
    .getElementById(
      "urlInput"
    )
    .value
    .split("\n")
    .filter(Boolean);

    if(urls.length === 0){

      alert(
        "Please enter URL"
      );

      return;
    }

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
        "URLs ingested successfully"
      );

    }else{

      alert(
        "URL ingestion failed"
      );
    }

  }catch(error){

    console.error(error);

    alert(
      "Backend connection failed"
    );
  }
}

/* FORGOT PASSWORD */

function openForgotPasswordModal(){

  document
  .getElementById("forgotModal")
  .classList.remove("hidden");
}

function closeForgotPasswordModal(){

  document
  .getElementById("forgotModal")
  .classList.add("hidden");
}

/* SEND OTP */

async function sendOTP(){

  try{

    const identifier =
    document
    .getElementById(
      "resetIdentifier"
    )
    .value;

    const response =
    await fetch(`${API}/send-otp`,{

      method:"POST",

      headers:{
        "Content-Type":
        "application/json"
      },

      body:JSON.stringify({
        identifier
      })
    });

    const data =
    await response.json();

    alert(
      data.message ||
      "OTP Sent"
    );

  }catch(error){

    console.error(error);

    alert(
      "Failed to send OTP"
    );
  }
}

/* RESET PASSWORD */

async function resetPassword(){

  try{

    const identifier =
    document
    .getElementById(
      "resetIdentifier"
    )
    .value;

    const otp =
    document
    .getElementById(
      "otpInput"
    )
    .value;

    const newPassword =
    document
    .getElementById(
      "newPassword"
    )
    .value;

    const confirmPassword =
    document
    .getElementById(
      "confirmPassword"
    )
    .value;

    const passwordRegex =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{4,}$/;

    if(!passwordRegex.test(newPassword)){

      alert(
        "Password must contain uppercase, lowercase, number, special character and minimum 4 characters"
      );

      return;
    }

    if(newPassword !== confirmPassword){

      alert(
        "Passwords do not match"
      );

      return;
    }

    const response =
    await fetch(`${API}/reset-password`,{

      method:"POST",

      headers:{
        "Content-Type":
        "application/json"
      },

      body:JSON.stringify({

        identifier,
        otp,
        new_password:newPassword
      })
    });

    const data =
    await response.json();

    alert(
      data.message ||
      "Password reset successful"
    );

    closeForgotPasswordModal();

  }catch(error){

    console.error(error);

    alert(
      "Password reset failed"
    );
  }
}