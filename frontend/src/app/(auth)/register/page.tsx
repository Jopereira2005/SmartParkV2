"use client";
import Image from "next/image";
import Link from 'next/link'
import { useState } from "react";

import styled from "../style.module.scss";

import Input from '@/components/Auth/Input';

import { FacebookIcon } from "@/assets/Auth/Facebook";
import { GoogleIcon } from "@/assets/Auth/Google";
import { TwitterIcon } from "@/assets/Auth/Twitter";

export default function RegisterPage() {
  // const { login } = useAuth();
  const [firstname, setFirstname] = useState('');
  const [lastname, setLastname] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [alertProps, setAlertProps] = useState({ message: '', timeDuration: 0, type: 'success' as 'success' | 'error' });
  const [alertOpen, setAlertOpen] = useState(false)

  // const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    // try {
    //   const response = await userService.register(name, username, email, password);
    //   if (response.statusCode >= 400) {
    //     throw response;
    //   }
      
    //   setEmail('');
    //   setPassword('');
    //   setName('');
    //   setUsername('');

    //   setAlertProps({
    //     message: "Usuario cadastrado com sucesso",
    //     timeDuration: 3000,
    //     type: "success"
    //   })

    //   setTimeout(() => {
    //     navigate("/login");
    //   }, 3500)

    //   setAlertOpen(true);
    // } catch (err: any) {
    //   setAlertProps({
    //     message: err.content ? String(err.content) : "Erro ao logar",
    //     timeDuration: 3000,
    //     type: "error"
    //   })
    //   setAlertOpen(true);
    // }
  };

  return (
    <div className={ styled.auth }>
      <div className={ styled.background }>
        <div className={ styled.main }>
          <div className={ styled.main__welcome }>
            <Link href='/'>
              <Image
                className={ styled.main__welcome__image }
                src="/logo.svg"
                alt="Logo"
                width={170}
                height={142}
                priority
              />
            </Link>
            <h1 className={ styled.main__welcome__text }>Bem-vindo ao <span>SmartPark!</span></h1>
          </div>

          <div className={ styled.main__div }></div>

          <div className={ styled.main__auth }>
              <h1 className={ styled.main__auth__title }>Cadastro</h1>
              <form autoComplete='false' onSubmit={ handleRegister } className={ styled.main__auth__form }>
                <div className={ styled.main__auth__form__inputs }>
                  <Input
                    type="text"
                    name="firstname"
                    label="Nome"
                    value={ firstname }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setFirstname(e.target.value) }
                  />

                  <Input
                    type="text"
                    name="lastname"
                    label="Sobrenome"
                    value={ lastname }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setLastname(e.target.value) }
                  />

                  <Input
                    type="text"
                    name="username"
                    label="Nome de usuário"
                    value={ username }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value) }
                  />

                  <Input
                    type="email"
                    name="email"
                    label="Email"
                    value={ email }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value) }
                  />

                  <Input
                    type="password"
                    name="password"
                    label="Senha"
                    value={ password }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value) }
                  />
                </div>

                <button type="submit" className={ styled.main__auth__button }>Cadastrar</button>
                <Link href="/login" className={ styled.main__auth__link }>Entrar</Link>
              </form>
            </div>

          <div className={ styled.main__social_medias }>
            <p className={ styled.main__social_medias__text }>Entrar com</p>
            <div className={ styled.main__social_medias__icons }>
              <div className={ styled.main__social_medias__icons__icon_container }>
                <FacebookIcon className={ styled.main__social_medias__icons__icon_container__icon }/>
              </div>
              <div className={ styled.main__social_medias__icons__icon_container }>
                <GoogleIcon className={ styled.main__social_medias__icons__icon_container__icon }/>
              </div>
              <div className={ styled.main__social_medias__icons__icon_container }>
                <TwitterIcon className={ styled.main__social_medias__icons__icon_container__icon }/>
              </div>
            </div>
          </div>  
        </div>
      </div>
    </div>
  );
}
