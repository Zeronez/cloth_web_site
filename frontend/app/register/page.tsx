import { AuthPage } from "../../components/auth/auth-page";

export const metadata = {
  title: "Регистрация"
};

export default function RegisterRoute() {
  return <AuthPage mode="register" />;
}
