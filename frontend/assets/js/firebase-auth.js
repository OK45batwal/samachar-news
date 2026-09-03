// Firebase SDK Configuration & Authentication Service for Samachar Truth Intelligence

const firebaseConfig = {
  apiKey: "AIzaSyDn9DGb90HTi-gXtr0Ez1p7fMlqICFN_Zk",
  authDomain: "samachar-news-2026.firebaseapp.com",
  projectId: "samachar-news-2026",
  storageBucket: "samachar-news-2026.firebasestorage.app",
  messagingSenderId: "601862635648",
  appId: "1:601862635648:web:ea6cf77c5c3198594be665"
};

let firebaseAuthInstance = null;

function getFirebaseAuth() {
  if (typeof firebase === 'undefined') return null;
  if (!firebase.apps || !firebase.apps.length) {
    try {
      firebase.initializeApp(firebaseConfig);
    } catch (e) {
      console.warn('Firebase init error:', e);
    }
  }
  if (!firebaseAuthInstance && firebase.auth) {
    firebaseAuthInstance = firebase.auth();
  }
  return firebaseAuthInstance;
}

// 1. Create Account & Dispatch Native Firebase Verification Email
async function registerWithEmailVerification(fullName, email, password) {
  const auth = getFirebaseAuth();
  if (!auth) {
    throw new Error('Firebase Authentication SDK is loading. Please try again.');
  }

  try {
    // Create user in Firebase Auth
    const userCredential = await auth.createUserWithEmailAndPassword(email, password);
    const user = userCredential.user;

    // Update display name
    if (fullName && user.updateProfile) {
      await user.updateProfile({ displayName: fullName }).catch(() => {});
    }

    // Send official Google/Firebase verification email
    const actionCodeSettings = {
      url: window.location.origin + '/home.html',
      handleCodeInApp: true
    };
    await user.sendEmailVerification(actionCodeSettings);

    return {
      status: 'success',
      user: user,
      message: `Verification email dispatched to ${email}`
    };
  } catch (error) {
    let msg = error.message || 'Registration failed.';
    if (error.code === 'auth/email-already-in-use') {
      msg = 'An account with this email address already exists. Please sign in instead.';
    } else if (error.code === 'auth/weak-password') {
      msg = 'Password is too weak. Please use at least 6 characters.';
    } else if (error.code === 'auth/invalid-email') {
      msg = 'Please enter a valid email address.';
    }
    throw new Error(msg);
  }
}

// 2. Resend Firebase Verification Email
async function resendFirebaseVerificationEmail() {
  const auth = getFirebaseAuth();
  if (!auth || !auth.currentUser) {
    throw new Error('No active user session found. Please register or sign in again.');
  }
  const actionCodeSettings = {
    url: window.location.origin + '/home.html',
    handleCodeInApp: true
  };
  await auth.currentUser.sendEmailVerification(actionCodeSettings);
  return { status: 'success', message: 'Verification email resent successfully.' };
}

// 3. Check if user clicked email verification link
async function checkUserEmailVerified() {
  const auth = getFirebaseAuth();
  if (!auth || !auth.currentUser) return false;
  await auth.currentUser.reload();
  return auth.currentUser.emailVerified;
}

// 4. Sign in with Firebase Auth
async function loginWithFirebaseAuth(email, password) {
  const auth = getFirebaseAuth();
  if (!auth) {
    throw new Error('Firebase Authentication SDK loading...');
  }

  try {
    const userCredential = await auth.signInWithEmailAndPassword(email, password);
    const user = userCredential.user;

    const token = await user.getIdToken();
    const username = email.split('@')[0];
    const userObj = {
      id: user.uid,
      email: user.email,
      username: username,
      full_name: user.displayName || username.toUpperCase() + ' (Verified Reader)',
      role: 'user',
      emailVerified: user.emailVerified,
      session_created: new Date().toISOString()
    };

    localStorage.setItem('samachar_token', 'firebase_' + token);
    localStorage.setItem('samachar_user', JSON.stringify(userObj));
    return userObj;
  } catch (error) {
    let msg = error.message || 'Invalid email or password.';
    if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password' || error.code === 'auth/invalid-credential') {
      msg = 'Invalid email or password. Please try again.';
    } else if (error.code === 'auth/too-many-requests') {
      msg = 'Too many failed login attempts. Please try again in a few minutes.';
    }
    throw new Error(msg);
  }
}

// 5. Delete Firebase Account
async function deleteFirebaseAccount() {
  const auth = getFirebaseAuth();
  if (auth && auth.currentUser) {
    try {
      await auth.currentUser.delete();
    } catch (_) {}
  }
  localStorage.removeItem('samachar_token');
  localStorage.removeItem('samachar_user');
  sessionStorage.clear();
}
