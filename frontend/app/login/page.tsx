import { AuthPage } from "../../components/auth/auth-page";

export const metadata = {
  title: "Вход"
};

export default function LoginRoute() {
  return <AuthPage mode="login" />;
}
