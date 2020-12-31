import Head from "next/head";
import dynamic from "next/dynamic";
import Base from "../components/Base";
import styles from "../styles/Home.module.css";
import { PropsWithoutRef } from "react";
import { GetServerSideProps } from "next";
import AES from "crypto-js/aes";

const PostMonacoEditor = dynamic(() => import("../components/EditorTabs"), {
  ssr: false,
});

export default function Home(
  props: PropsWithoutRef<{ initialData; encryptedPayload }>
) {
  const { initialData, encryptedPayload } = props;

  return (
    <div>
      <Head>
        <title>MystBin</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Base className={styles.Tabs}>
        <PostMonacoEditor
          initialData={initialData}
          encryptedPayload={encryptedPayload}
        />
      </Base>
    </div>
  );
}

export const getServerSideProps: GetServerSideProps = async () => {
  const password = "abc";
  let initialData;
  let dummyData = [
    { title: "test.py", content: "print('Hello World!')" },
    { title: "other.py", content: "print('other.py')" },
  ];

  var encryptedPayload = AES.encrypt(
    JSON.stringify(dummyData),
    password
  ).toString();

  if (password) {
    initialData = [
      { title: "!protected!", content: "Password protected paste." },
    ];
  } else {
    initialData = dummyData;
  }

  return {
    props: {
      initialData,
      encryptedPayload,
    },
  };
};
