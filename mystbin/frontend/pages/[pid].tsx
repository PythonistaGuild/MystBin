import { GetServerSideProps } from "next";
import Head from "next/head";
import { useRouter } from "next/router";
import { PropsWithoutRef } from "react";
import styles from "../styles/Home.module.css";

export default function Home(props: PropsWithoutRef<{ authorized: boolean }>) {
  const { authorized } = props;
  const router = useRouter();
  const { pid } = router.query;

  return (
    <div className={styles.container}>
      <Head>
        <title>Create Next App</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>
      {authorized ? pid : "No."}
    </div>
  );
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  let authorized = false;

  return {
    props: {
      authorized,
    },
  };
};
