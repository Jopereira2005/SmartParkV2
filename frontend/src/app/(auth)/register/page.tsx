"use client";
import Image from "next/image";
import Link from 'next/link'
import { useRouter } from "next/navigation";
import { useState } from "react";

import styled from "../style.module.scss";

import Input from '@/components/Auth/Input';
import AlertNotification from "@/components/Common/AlertNotification";

import { FacebookIcon } from "@/assets/Auth/Facebook";
import { GoogleIcon } from "@/assets/Auth/Google";
import { TwitterIcon } from "@/assets/Auth/Twitter";

import { register } from "@/lib/auth/register";

export default function RegisterPage() {
  const router = useRouter();
  const [credentials, setCredentials] = useState({ username: '', email: '', first_name: '', last_name: '',  password: '', password_confirm: '' });

  const [alertProps, setAlertProps] = useState({ message: '', timeDuration: 0, type: 'success' as 'success' | 'error' });
  const [alertOpen, setAlertOpen] = useState(false)

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await register(credentials);

      if (!response.ok) {
        throw response;
      }
      
      setCredentials({ username: '', email: '', first_name: '', last_name: '',  password: '', password_confirm: '' });

      setAlertProps({
        message: "Usuario cadastrado com sucesso",
        timeDuration: 2000,
        type: "success"
      })

      setTimeout(() => {
        router.replace("/");
      }, 2500)

      setAlertOpen(true);
    } catch (err: any) {
      console.log(err);
      setAlertProps({
        message: err.message[0],
        timeDuration: 3000,
        type: "error"
      })
      setAlertOpen(true);
    }
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
                    name="first_name"
                    label="Nome"
                    value={ credentials.first_name }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setCredentials({ ...credentials, first_name: e.target.value }) }
                  />

                  <Input
                    type="text"
                    name="last_name"
                    label="Sobrenome"
                    value={ credentials.last_name }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setCredentials({ ...credentials, last_name: e.target.value }) }
                  />

                  <Input
                    type="text"
                    name="username"
                    label="Nome de usuário"
                    value={ credentials.username }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setCredentials({ ...credentials, username: e.target.value }) }
                  />

                  <Input
                    type="email"
                    name="email"
                    label="Email"
                    value={ credentials.email }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setCredentials({ ...credentials, email: e.target.value }) }
                  />

                  <Input
                    type="password"
                    name="password"
                    label="Senha"
                    value={ credentials.password }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setCredentials({ ...credentials, password: e.target.value }) }
                  />

                  <Input
                    type="password"
                    name="confirmPassword"
                    label="Confirmar Senha"
                    value={ credentials.password_confirm }
                    onChangeFunc={ (e: React.ChangeEvent<HTMLInputElement>) => setCredentials({ ...credentials, password_confirm: e.target.value }) }
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
      <AlertNotification
        {...alertProps}
        state={ alertOpen }
        handleClose={() => setAlertOpen(false)}      
      />
    </div>
  );
}
