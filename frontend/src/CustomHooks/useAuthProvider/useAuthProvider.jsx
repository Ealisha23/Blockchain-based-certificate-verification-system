import { useState, useMemo, useCallback } from "react";
import jwtDecode from "jwt-decode";

const TOKEN_KEY = "appCertificate";

const decodeToken = (token) => {
  if (!token) return null;
  try {
    const decoded = jwtDecode(token);
    // Reject expired tokens
    return decoded.exp > Date.now() / 1000 ? decoded : null;
  } catch (error) {
    return null;
  }
};

function useAuthenticator() {
  const [token, setTokenState] = useState(localStorage.getItem(TOKEN_KEY));
  const [loggedOut, setLoggedOut] = useState(false);

  const decode = useMemo(
    () => (loggedOut ? null : decodeToken(token)),
    [token, loggedOut]
  );

  // Components call setToken(localStorage.getItem(...)) after login and
  // setToken(null) on logout.
  const setToken = useCallback((value) => {
    setLoggedOut(false);
    setTokenState(value);
  }, []);

  // Kept for backwards compatibility: setAuthenticated(false) signs out.
  const setAuthenticated = useCallback((value) => {
    if (!value) setLoggedOut(true);
  }, []);

  return {
    token,
    authenticated: !!decode,
    firstName: decode?.first_name,
    lastName: decode?.last_name,
    userId: decode?.user_id,
    userRole: decode?.role,
    setAuthenticated,
    setToken,
  };
}

export default useAuthenticator;
