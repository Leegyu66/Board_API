// -----------------------------
//  app.js
// -----------------------------

// ★ CORS 환경에서 쿠키 전송을 허용하려면
axios.defaults.withCredentials = true;   // 모든 요청에 쿠키/인증정보 포함

const API_URL = "http://192.168.100.145:8080";  // 백엔드 API 주소 (필요에 따라 수정)

// DOM 요소들
const loginForm = document.getElementById("loginForm");
const logoutButton = document.getElementById("logoutButton");
const boardSection = document.getElementById("boardSection");
const boardList = document.getElementById("boardList");
const createPostButton = document.getElementById("createPostButton");
const createPostForm = document.getElementById("createPostForm");
const submitPostButton = document.getElementById("submitPostButton");
const cancelPostButton = document.getElementById("cancelPostButton");
const postTitleInput = document.getElementById("postTitle");
const postContentInput = document.getElementById("postContent");
const editPostButton = document.getElementById("editPostButton");
const detailTitle = document.getElementById("detailTitle");
const detailContent = document.getElementById("detailContent");
const postDetails = document.getElementById("postDetails");
const detailViewcnt = document.getElementById("detailViewcnt");
const closePostDetailsButton = document.getElementById("closePostDetails");

// 회원가입 관련
const showSignupFormButton = document.getElementById("showSignupForm");
const signupForm = document.getElementById("signupForm");
const cancelSignupButton = document.getElementById("cancelSignupButton");

// 현재 수정 중인 글 ID
let currentPostId = null;

/* ------------------------------------------------
   사용자 정보 불러오기: GET /user
   -> { name: "홍길동", ... }
------------------------------------------------- */
async function loadUserName() {
  try {
    const response = await axios.get(`${API_URL}/user`, {
      headers: { "Authorization": `Bearer ${getCookie("access_token")}` },
    });
    // 예: { "name": "홍길동" }
    const userName = response.data.name;
    const loggedUserSpan = document.getElementById("loggedUser");
    loggedUserSpan.textContent = userName ? `(${userName})` : "";
  } catch (error) {
    console.error("Failed to load user info:", error);
  }
}

/* ----------------------------
   (A) 회원가입 로직
---------------------------- */
showSignupFormButton.addEventListener("click", () => {
  signupForm.style.display = "block";
});

cancelSignupButton.addEventListener("click", () => {
  signupForm.style.display = "none";
  document.getElementById("name").value = "";
  document.getElementById("email").value = "";
  document.getElementById("loginId").value = "";
  document.getElementById("password").value = "";
});

signupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const nameValue = document.getElementById("name").value;
  const emailValue = document.getElementById("email").value;
  const loginIdValue = document.getElementById("loginId").value;
  const passwordValue = document.getElementById("signupPassword").value;

  if (!nameValue || !emailValue || !loginIdValue || !passwordValue) {
    alert("All fields are required.");
    return;
  }

  const payload = {
    name: nameValue,
    email: emailValue,
    login_id: loginIdValue,
    password: passwordValue,
  };

  try {
    await axios.post(`${API_URL}/user`, payload);
    alert("Sign Up Success!");
    signupForm.style.display = "none";
    document.getElementById("name").value = "";
    document.getElementById("email").value = "";
    document.getElementById("loginId").value = "";
    document.getElementById("signupPassword").value = "";
  } catch (error) {
    alert("Sign Up failed!");
    console.error(error);
  }
});

/* ----------------------------
   (B) 로그인 로직
---------------------------- */
loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const loginData = new URLSearchParams();
    loginData.append("username", username);
    loginData.append("password", password);

    const response = await axios.post(
      `${API_URL}/user/login`,
      loginData,
      {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      }
    );

    // 토큰을 쿠키로 저장 (서버에서 Set-Cookie를 안 주는 구조라면)
    document.cookie = `access_token=${response.data.access_token}; path=/;`;

    // UI 전환
    loginForm.style.display = "none";
    signupForm.style.display = "none";
    showSignupFormButton.style.display = "none";

    boardSection.style.display = "block";
    logoutButton.style.display = "inline-block";
    
    // ★ 로그인 후 사용자 이름 표시
    await loadUserName();

    // 게시판 글 목록
    loadBoardPosts();
  } catch (error) {
    alert("Login failed!");
    console.error(error);
  }
});

/* ----------------------------
   (C) 로그아웃
---------------------------- */
logoutButton.addEventListener("click", async () => {
  try {
    await axios.post(
      `${API_URL}/user/logout`,
      {},
      {
        headers: { "Authorization": `Bearer ${getCookie("access_token")}` },
      }
    );
    
    // 쿠키 제거
    document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    
    // UI 전환
    boardSection.style.display = "none";
    logoutButton.style.display = "none";
    showSignupFormButton.style.display = "inline-block";
    loginForm.style.display = "block";

    // 사용자 이름 표시 제거
    document.getElementById("loggedUser").textContent = "";
  } catch (error) {
    alert("Logout failed!");
    console.error(error);
  }
});

/* ----------------------------
   (D) 게시판 로직
---------------------------- */
async function loadBoardPosts() {
  try {
    const response = await axios.get(`${API_URL}/board`, {
      headers: { "Authorization": `Bearer ${getCookie("access_token")}` },
    });

    boardList.innerHTML = "";
    response.data.forEach(post => {
      const listItem = document.createElement("li");

      // 글 제목 옆에 작성자 표시
      listItem.textContent = `${post.title} (작성자: ${post.name})`;

      // 상세보기
      listItem.addEventListener("click", async () => {
        // 토글 열기/닫기
        if (postDetails.style.display !== "none" && currentPostId === post.id) {
          postDetails.style.display = "none";
          currentPostId = null;
          return;
        }

        // 상세 보기
        try {
          const res = await axios.get(`${API_URL}/board/${post.id}`, {
            headers: { "Authorization": `Bearer ${getCookie("access_token")}` },
          });
          const board = res.data;
          currentPostId = post.id;

          detailTitle.textContent = `${board.title} (작성자: ${board.name})`;
          detailContent.textContent = board.content;
          detailViewcnt.textContent = `View Count: ${board.view_cnt}`;
          postDetails.style.display = "block";
        } catch (error) {
          alert("글을 불러오는 데 실패!");
          console.error(error);
        }
      });

      // 삭제 버튼
      const deleteButton = document.createElement("button");
      deleteButton.textContent = "삭제";
      deleteButton.style.marginLeft = "10px";
      deleteButton.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (confirm("정말 삭제하시겠습니까?")) {
          try {
            await axios.delete(`${API_URL}/board/${post.id}`, {
              headers: { "Authorization": `Bearer ${getCookie("access_token")}` },
            });
            alert("삭제 완료!");
            postDetails.style.display = "none";
            loadBoardPosts();
          } catch (error) {
            alert("삭제 실패!");
            console.error(error);
          }
        }
      });

      listItem.appendChild(deleteButton);
      boardList.appendChild(listItem);
    });
  } catch (error) {
    alert("Failed to load board posts");
    console.error(error);
  }
}

// 상세 보기 닫기
closePostDetailsButton.addEventListener("click", () => {
  postDetails.style.display = "none";
});

// 글 작성 폼 열기
createPostButton.addEventListener("click", () => {
  createPostForm.style.display = "block";
  submitPostButton.textContent = "Submit";
  currentPostId = null;
});

// 글 작성/수정
submitPostButton.addEventListener("click", async () => {
  const title = postTitleInput.value;
  const content = postContentInput.value;

  if (!title || !content) {
    alert("Both title and content are required.");
    return;
  }

  try {
    if (currentPostId) {
      // 수정
      await axios.patch(
        `${API_URL}/board/${currentPostId}`,
        { title, content },
        { headers: { "Authorization": `Bearer ${getCookie("access_token")}` } }
      );
      alert("수정 완료!");
    } else {
      // 새 글 작성
      await axios.post(
        `${API_URL}/board`,
        { title, content },
        { headers: { "Authorization": `Bearer ${getCookie("access_token")}` } }
      );
      alert("작성 완료!");
    }
    // 폼 초기화
    postTitleInput.value = "";
    postContentInput.value = "";
    createPostForm.style.display = "none";
    submitPostButton.textContent = "Submit";
    currentPostId = null;

    loadBoardPosts();
  } catch (error) {
    alert("등록 실패!");
    console.error(error);
  }
});

// 글 작성 취소
cancelPostButton.addEventListener("click", () => {
  createPostForm.style.display = "none";
  submitPostButton.textContent = "Submit";
  currentPostId = null;
});

// 글 수정 버튼 (상세 보기 영역)
editPostButton.addEventListener("click", () => {
  if (!currentPostId) return;
  postTitleInput.value = detailTitle.textContent.replace(/\(작성자:.*\)$/, "").trim();
  postContentInput.value = detailContent.textContent;
  createPostForm.style.display = "block";
  submitPostButton.textContent = "Update";
  postDetails.style.display = "none";
});

/* ----------------------------
   (E) 쿠키 가져오기 헬퍼
---------------------------- */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return null;
}